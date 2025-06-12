from datetime import datetime
from enum import Enum
from typing import Optional, List
from beanie import Document
from pydantic import Field


class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewCategory(str, Enum):
    QUALITY = "quality"
    SERVICE = "service"
    PRICING = "pricing"
    DELIVERY = "delivery"
    USABILITY = "usability"
    COMMUNICATION = "communication"
    PERFORMANCE = "performance"
    SUPPORT = "support"
    EXPERIENCE = "experience"
    OTHER = "other"


class Review(Document):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    review_text: str = Field(..., min_length=1)
    ai_processed: bool = Field(default=False)
    ai_processing_error: Optional[str] = None
    ai_analysis_data: Optional[dict] = None
    email_sent: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "reviews"
        indexes = [
            "customer_email",
            "created_at",
            "ai_processed",
            "email_sent"
        ]
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, customer={self.customer_name})>" 