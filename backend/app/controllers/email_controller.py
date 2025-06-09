import logging
from fastapi import HTTPException
from app.services.email_service import test_email_connection

logger = logging.getLogger(__name__)


async def test_email_service():
    """Test email service connection"""
    try:
        is_connected = await test_email_connection()
        return {
            "email_service": "connected" if is_connected else "disconnected",
            "message": "Email service test completed"
        }
    except Exception as e:
        logger.error(f"❌ Email test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}") 