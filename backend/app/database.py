from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# MongoDB client
client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    """Create database connection"""
    global client, database
    try:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(settings.mongodb_url)
        database = client[settings.mongodb_database]
        
        # Test connection
        await client.admin.command('ping')
        logger.info("✅ Connected to MongoDB successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return False


async def close_mongo_connection():
    """Close database connection"""
    global client
    if client:
        client.close()
        logger.info("👋 Disconnected from MongoDB")


async def init_database():
    """Initialize database with Beanie"""
    from app.models.review import Review
    
    try:
        await init_beanie(
            database=database,
            document_models=[Review]
        )
        logger.info("✅ Beanie initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Beanie: {e}")
        return False


async def get_database():
    """Get database instance"""
    return database


async def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        if client:
            await client.admin.command('ping')
            return True
        return False
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# For backward compatibility during migration
def get_db():
    """Deprecated: MongoDB doesn't need session management like SQLAlchemy"""
    pass 