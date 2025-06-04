from fastapi import APIRouter
from app.controllers.health_controller import get_health_check

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint - returns 204 if healthy"""
    return await get_health_check() 