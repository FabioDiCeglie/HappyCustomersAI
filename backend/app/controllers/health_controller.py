import logging
from fastapi import Response

logger = logging.getLogger(__name__)


async def get_health_check():
    """Health check endpoint - returns 204 if healthy"""
    return Response(status_code=204) 