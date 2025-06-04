from fastapi import APIRouter
from .health import router as health_router
from .reviews import router as reviews_router
from .analytics import router as analytics_router
from .email import router as email_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health_router, tags=["health"])
api_router.include_router(reviews_router, prefix="/api/v1/reviews", tags=["reviews"])
api_router.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
api_router.include_router(email_router, prefix="/api/v1/email", tags=["email"]) 