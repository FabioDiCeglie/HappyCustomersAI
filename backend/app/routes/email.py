from fastapi import APIRouter
from app.controllers.email_controller import test_email_service

router = APIRouter()


@router.post("/test")
async def test_email_service_route():
    """Test email service connection"""
    return await test_email_service() 