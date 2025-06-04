from fastapi import APIRouter
from app.controllers.analytics_controller import get_dashboard_analytics

router = APIRouter()


@router.get("/dashboard")
async def dashboard_analytics():
    """Get comprehensive analytics data for dashboard"""
    return await get_dashboard_analytics() 