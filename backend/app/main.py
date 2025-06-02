from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.database import connect_to_mongo, close_mongo_connection, init_database, check_database_connection
from app.services.review_service import review_service
from app.services.email_service import email_service
from app.agents.review_agent import review_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting AI Customer Feedback Management System")
    
    # Initialize MongoDB
    mongo_connected = await connect_to_mongo()
    logger.info(f"🗄️  MongoDB: {'✅ Connected' if mongo_connected else '❌ Connection failed'}")
    
    if mongo_connected:
        beanie_initialized = await init_database()
        logger.info(f"📄 Beanie: {'✅ Initialized' if beanie_initialized else '❌ Initialization failed'}")
    
    # Test email service (optional)
    # email_healthy = await email_service.test_connection()
    # logger.info(f"📧 Email service: {'✅ Connected' if email_healthy else '❌ Connection failed'}")
    
    logger.info(f"🤖 AI Agent initialized with Gemini Pro")
    logger.info("🎉 Application startup complete!")
    
    yield
    
    logger.info("👋 Shutting down application")
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="AI Customer Feedback Management System",
    description="Automatically analyze customer reviews and send personalized follow-up emails",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Customer Feedback Management System",
        "status": "running",
        "version": "1.0.0",
        "restaurant": settings.restaurant_name
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    db_healthy = await check_database_connection()
    
    return {
        "status": "healthy",
        "ai_agent": "ready",
        "database": "connected" if db_healthy else "disconnected",
        "email_service": "ready"
    }


# Pydantic models for API
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReviewCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    customer_phone: Optional[str] = Field(None, max_length=50)
    review_text: str = Field(..., min_length=10)
    rating: Optional[int] = Field(None, ge=1, le=5)
    visit_date: Optional[datetime] = None
    table_number: Optional[str] = Field(None, max_length=20)
    order_number: Optional[str] = Field(None, max_length=50)


class ReviewResponse(BaseModel):
    id: str
    customer_name: str
    customer_email: str
    review_text: str
    rating: Optional[int]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    urgency_level: Optional[str]
    categories: Optional[List[str]]
    key_issues: Optional[List[str]]
    email_sent: bool
    email_template_used: Optional[str]
    created_at: datetime
    ai_processed: bool

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    sentiment: str
    sentiment_score: float
    urgency_level: str
    categories: List[str]
    key_issues: List[str]
    should_send_email: bool
    email_template: Optional[str]
    analysis_complete: bool
    error: str

@app.post("/api/v1/reviews", response_model=dict)
async def create_review(review: ReviewCreate):
    """Create a new review and process it through the complete AI + email workflow"""
    try:
        logger.info(f"📝 Creating new review from {review.customer_name}")
        
        result = await review_service.create_and_process_review(
            customer_name=review.customer_name,
            customer_email=review.customer_email,
            customer_phone=review.customer_phone,
            review_text=review.review_text,
            rating=review.rating,
            visit_date=review.visit_date,
            table_number=review.table_number,
            order_number=review.order_number
        )
        
        logger.info(f"✅ Review processed successfully - ID: {result['review_id']}")
        
        # Analyze the review after it's created
        try:
            logger.info(f"🔍 Analyzing review from {review.customer_name}")
            
            analysis_result = await review_agent.analyze_review(
                review_text=review.review_text,
                customer_name=review.customer_name,
                rating=review.rating
            )
            
            logger.info(f"✅ Analysis complete: {analysis_result['sentiment']} sentiment, {analysis_result['urgency_level']} urgency")
            
            # Combine creation result with analysis result
            result.update({
                'analysis': analysis_result,
                'analysis_complete': True
            })
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            result.update({
                'analysis': None,
                'analysis_complete': False,
                'analysis_error': str(e)
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Review creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Review creation failed: {str(e)}")


@app.get("/api/v1/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    skip: int = 0,
    limit: int = 100,
    sentiment: Optional[str] = None,
    urgency: Optional[str] = None,
    email_sent: Optional[bool] = None
):
    """Get reviews with optional filtering"""
    try:
        reviews = await review_service.get_reviews(
            skip=skip,
            limit=limit,
            sentiment=sentiment,
            urgency=urgency,
            email_sent=email_sent
        )
        
        # Convert MongoDB documents to response format
        response_reviews = []
        for review in reviews:
            response_reviews.append(ReviewResponse(
                id=str(review.id),
                customer_name=review.customer_name,
                customer_email=review.customer_email,
                review_text=review.review_text,
                rating=review.rating,
                sentiment=review.sentiment,
                sentiment_score=review.sentiment_score,
                urgency_level=review.urgency_level,
                categories=review.categories,
                key_issues=review.key_issues,
                email_sent=review.email_sent,
                email_template_used=review.email_template_used,
                created_at=review.created_at,
                ai_processed=review.ai_processed
            ))
        
        return response_reviews
    except Exception as e:
        logger.error(f"❌ Failed to fetch reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch reviews: {str(e)}")

@app.post("/api/v1/email/test")
async def test_email_service():
    """Test email service connection"""
    try:
        is_connected = await email_service.test_connection()
        return {
            "email_service": "connected" if is_connected else "disconnected",
            "message": "Email service test completed"
        }
    except Exception as e:
        logger.error(f"❌ Email test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 