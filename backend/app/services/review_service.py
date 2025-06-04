from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId
import logging

from app.models.review import Review, SentimentType, UrgencyLevel
from app.agents.review_agent import review_agent
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class ReviewService:
    
    async def create_and_process_review(
        self,
        customer_name: str,
        customer_email: str,
        review_text: str,
        rating: Optional[int] = None,
        customer_phone: Optional[str] = None,
        visit_date: Optional[datetime] = None,
        table_number: Optional[str] = None,
        order_number: Optional[str] = None,
        review_source: str = "manual"
    ) -> Dict[str, Any]:
        """Create a new review and process it through the complete AI + email workflow"""
        
        try:
            logger.info(f"🆕 Processing new review from {customer_name}")
            
            # Create new review document
            review = Review(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                review_text=review_text,
                rating=rating,
                visit_date=visit_date,
                table_number=table_number,
                order_number=order_number,
                review_source=review_source,
                created_at=datetime.utcnow()
            )
            
            # Save to MongoDB
            await review.save()
            
            logger.info(f"💾 Review saved to database with ID: {review.id}")
            
            # Analyze with AI
            analysis_result = await self._analyze_review(review)
            
            # Send email if needed
            email_result = await self._send_email_if_needed(review)
            
            return {
                "review_id": str(review.id),
                "customer_name": review.customer_name,
                "customer_email": review.customer_email,
                "analysis": analysis_result,
                "email_sent": email_result.get("sent", False),
                "email_template": email_result.get("template"),
                "message": "Review processed successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process review: {str(e)}")
            raise
    
    async def _analyze_review(self, review: Review) -> Dict[str, Any]:
        """Analyze review with AI agent"""
        try:
            logger.info(f"🧠 Analyzing review {review.id} with AI")
            
            analysis = await review_agent.analyze_review(
                review_text=review.review_text,
                customer_name=review.customer_name,
                rating=review.rating
            )
            
            # Update review with analysis results
            review.sentiment = analysis["sentiment"]
            review.sentiment_score = analysis["sentiment_score"]
            review.urgency_level = analysis["urgency_level"]
            review.categories = analysis["categories"]
            review.key_issues = analysis["key_issues"]
            review.ai_processed = True
            review.ai_analysis_data = analysis
            review.updated_at = datetime.utcnow()
            
            if analysis.get("error"):
                review.ai_processing_error = analysis["error"]
            
            await review.save()
            
            logger.info(f"✅ AI analysis complete: {analysis['sentiment']} sentiment, {analysis['urgency_level']} urgency")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed for review {review.id}: {str(e)}")
            review.ai_processing_error = str(e)
            review.ai_processed = False
            await review.save()
            raise
    
    async def _send_email_if_needed(self, review: Review) -> Dict[str, Any]:
        """Send follow-up email if the AI determined it's needed"""
        
        result = {"sent": False, "template": None, "error": None}
        
        try:
            # Check if email should be sent based on AI analysis
            analysis_data = review.ai_analysis_data or {}
            should_send = analysis_data.get("should_send_email", False)
            email_template = analysis_data.get("email_template")
            
            if not should_send or not email_template:
                logger.info(f"📧 No email needed for review {review.id}")
                return result
            
            logger.info(f"📧 Sending {email_template} email for review {review.id}")
            
            # Send the email
            email_sent = await email_service.send_email(
                to_email=review.customer_email,
                customer_name=review.customer_name,
                template_name=email_template,
                key_issues=review.key_issues or []
            )
            
            if email_sent:
                # Update review record
                review.email_sent = True
                review.email_sent_at = datetime.utcnow()
                review.email_template_used = email_template
                review.updated_at = datetime.utcnow()
                
                await review.save()
                
                result["sent"] = True
                result["template"] = email_template
                
                logger.info(f"✅ Email sent successfully for review {review.id}")
            else:
                result["error"] = "Failed to send email"
                logger.error(f"❌ Failed to send email for review {review.id}")
            
        except Exception as e:
            logger.error(f"❌ Email sending error for review {review.id}: {str(e)}")
            result["error"] = str(e)
        
        return result
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics data for dashboard"""
        
        # Total reviews
        total_reviews = await Review.count()
        
        # Sentiment breakdown
        sentiment_pipeline = [
            {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
        ]
        sentiment_results = await Review.aggregate(sentiment_pipeline).to_list(None)
        sentiment_breakdown = {item["_id"]: item["count"] for item in sentiment_results if item["_id"]}
        
        # Urgency breakdown
        urgency_pipeline = [
            {"$group": {"_id": "$urgency_level", "count": {"$sum": 1}}}
        ]
        urgency_results = await Review.aggregate(urgency_pipeline).to_list(None)
        urgency_breakdown = {item["_id"]: item["count"] for item in urgency_results if item["_id"]}
        
        # Email stats
        emails_sent = await Review.find({"email_sent": True}).count()
        
        # Recent reviews (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_reviews = await Review.find({"created_at": {"$gte": week_ago}}).count()
        
        return {
            "total_reviews": total_reviews,
            "recent_reviews": recent_reviews,
            "sentiment_breakdown": sentiment_breakdown,
            "urgency_breakdown": urgency_breakdown,
            "emails_sent": emails_sent,
            "email_rate": emails_sent / total_reviews if total_reviews > 0 else 0
        }

review_service = ReviewService() 