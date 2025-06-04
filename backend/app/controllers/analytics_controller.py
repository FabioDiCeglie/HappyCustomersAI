import logging
from fastapi import HTTPException
from app.services.review_service import review_service

logger = logging.getLogger(__name__)


async def get_dashboard_analytics():
    """Get comprehensive analytics data for dashboard"""
    try:
        analytics = await review_service.get_analytics()
        return analytics
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard analytics: {str(e)}") 