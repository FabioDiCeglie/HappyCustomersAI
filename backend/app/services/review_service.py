from datetime import datetime
from typing import Dict, Any
from app.models.review import Review
from app.agents.review_agent import analyze_review
import logging

logger = logging.getLogger(__name__)


async def create_and_process_review(
    customer_name: str,
    customer_email: str,
    review_text: str,
) -> Dict[str, Any]:
    """Create a new review or update existing one and process it through the complete AI + email workflow"""
    
    try:
        # Check if a review from this customer email already exists
        existing_review = await Review.find_one(Review.customer_email == customer_email)
        
        if existing_review:
            logger.info(f"🔄 Updating existing review for customer: {customer_name} ({customer_email})")
            is_update = True
        else:
            logger.info(f"🆕 Processing new review from {customer_name} ({customer_email})")
            is_update = False
        
        logger.info(f"🧠 Analyzing review with AI")

        analysis = await analyze_review(
            review_text=review_text,
            customer_name=customer_name,
            customer_email=customer_email,
            rating=None
        )
        
        if existing_review:
            existing_review.customer_name = customer_name
            existing_review.review_text = review_text
            existing_review.ai_processed = True
            existing_review.ai_processing_error = analysis.get("error", None)
            existing_review.ai_analysis_data = analysis
            existing_review.email_sent = analysis['email_sent']
            existing_review.updated_at = datetime.utcnow()
            
            review = existing_review
            await review.save()
            
            logger.info(f"💾 Updated existing review in database with ID: {review.id}")
        else:
            review = Review(
                customer_name=customer_name,
                customer_email=customer_email,
                review_text=review_text,
                ai_analysis_data=analysis,
                email_sent=analysis['email_sent'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await review.save()
            
            logger.info(f"💾 New review saved to database with ID: {review.id}")
        
        logger.info(f"✅ AI analysis complete: {analysis['sentiment']} sentiment, {analysis['urgency_level']} urgency")

        return {
            "review_id": str(review.id),
            "customer_name": review.customer_name,
            "customer_email": review.customer_email,
            "analysis": analysis,
            "email_sent": review.email_sent,
            "is_update": is_update,
            "message": f"Review {'updated' if is_update else 'created'} and processed successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process review: {str(e)}")
        raise