from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.database import connect_to_mongo, close_mongo_connection, init_database
from app.services.email_service import test_email_connection
from app.routes import api_router
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting AI Customer Feedback Management System")
    
    mongo_connected = await connect_to_mongo()
    logger.info(f"🗄️  MongoDB: {'✅ Connected' if mongo_connected else '❌ Connection failed'}")
    
    if mongo_connected:
        beanie_initialized = await init_database()
        logger.info(f"📄 Beanie: {'✅ Initialized' if beanie_initialized else '❌ Initialization failed'}")
    
    email_healthy = await test_email_connection()
    logger.info(f"📧 Email service: {'✅ Connected' if email_healthy else '❌ Connection failed'}")
    
    logger.info(f"🤖 AI Agent initialized with Gemini Pro")
    logger.info("🎉 Application startup complete!")
    
    yield
    
    logger.info("👋 Shutting down application")
    await close_mongo_connection()


app = FastAPI(
    title="AI Customer Feedback Management System",
    description="Automatically analyze customer reviews and send personalized follow-up emails",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 