from datetime import datetime
from typing import Dict, Any
from app.models.review import Review
from app.agents.review_agent import analyze_review
from app.services.email_service import send_email, test_email_connection
import logging

logger = logging.getLogger(__name__)


async def create_and_process_review(
    customer_name: str,
    customer_email: str,
    review_text: str,
) -> Dict[str, Any]:
    """Create a new review or update existing one and process it through the complete AI + email workflow"""
    
    try:
        # Check if a review from this customer email already exists
        existing_review = await Review.find_one(Review.customer_email == customer_email)
        
        if existing_review:
            logger.info(f"🔄 Updating existing review for customer: {customer_name} ({customer_email})")
            is_update = True
        else:
            logger.info(f"🆕 Processing new review from {customer_name} ({customer_email})")
            is_update = False
        
        logger.info(f"🧠 Analyzing review with AI")

        analysis = await analyze_review(
            review_text=review_text,
            customer_name=customer_name,
            rating=None
        )
        
        if existing_review:
            # Update existing review
            existing_review.customer_name = customer_name
            existing_review.review_text = review_text
            existing_review.sentiment = analysis["sentiment"]
            existing_review.sentiment_score = analysis["sentiment_score"]
            existing_review.urgency_level = analysis["urgency_level"]
            existing_review.categories = analysis["categories"]
            existing_review.key_issues = analysis["key_issues"]
            existing_review.ai_processed = True
            existing_review.ai_analysis_data = analysis
            existing_review.ai_processing_error = analysis.get("error", None)
            existing_review.updated_at = datetime.utcnow()
            
            review = existing_review
            await review.save()
            
            logger.info(f"💾 Updated existing review in database with ID: {review.id}")
        else:
            # Create new review
            review = Review(
                customer_name=customer_name,
                customer_email=customer_email,
                review_text=review_text,
                sentiment=analysis["sentiment"],
                sentiment_score=analysis["sentiment_score"],
                urgency_level=analysis["urgency_level"],
                categories=analysis["categories"],
                key_issues=analysis["key_issues"],
                ai_processed=True,
                ai_analysis_data=analysis,
                ai_processing_error=analysis.get("error", None),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await review.save()
            
            logger.info(f"💾 New review saved to database with ID: {review.id}")
        
        logger.info(f"✅ AI analysis complete: {analysis['sentiment']} sentiment, {analysis['urgency_level']} urgency")
        
        return {
            "review_id": str(review.id),
            "customer_name": review.customer_name,
            "customer_email": review.customer_email,
            "analysis": analysis,
            "email_sent": False,
            "email_template": None,
            "is_update": is_update,
            "message": f"Review {'updated' if is_update else 'created'} and processed successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process review: {str(e)}")
        raise


async def analyze_review_with_ai(review: Review) -> Dict[str, Any]:
    """Analyze review with AI agent (legacy function - now integrated into create_and_process_review)"""
    try:
        logger.info(f"🧠 Analyzing review {review.id} with AI")
        
        analysis = await analyze_review(
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


# async def send_email_if_needed(review: Review) -> Dict[str, Any]:
#     """Send email if the review requires it"""
#     try:
#         if not review.ai_processed or not review.ai_analysis_data:
#             logger.warning(f"⚠️ Review {review.id} not processed by AI yet")
#             return {"sent": False, "reason": "Review not analyzed yet"}
        
#         analysis = review.ai_analysis_data
#         should_send = analysis.get("should_send_email", False)
#         template = analysis.get("email_template")
        
#         if not should_send or not template:
#             logger.info(f"📧 No email needed for review {review.id}")
#             return {"sent": False, "reason": "Email not required"}
        
#         logger.info(f"📧 Sending {template} email for review {review.id}")
        
#         email_sent = await send_email(
#             to_email=review.customer_email,
#             customer_name=review.customer_name,
#             template_name=template,
#             key_issues=review.key_issues or []
#         )
        
#         if email_sent:
#             review.email_sent = True
#             review.email_sent_at = datetime.utcnow()
#             review.email_template_used = template
#             review.updated_at = datetime.utcnow()
#             await review.save()
            
#             logger.info(f"✅ Email sent successfully for review {review.id}")
#             return {"sent": True, "template": template}
#         else:
#             logger.error(f"❌ Failed to send email for review {review.id}")
#             return {"sent": False, "reason": "Email sending failed"}
        
#     except Exception as e:
#         logger.error(f"❌ Email processing failed for review {review.id}: {str(e)}")
#         return {"sent": False, "reason": f"Error: {str(e)}"}


async def get_review_stats() -> Dict[str, Any]:
    """Get review statistics"""
    try:
        total_reviews = await Review.count()
        
        # Count by sentiment
        positive_count = await Review.find(Review.sentiment == "positive").count()
        negative_count = await Review.find(Review.sentiment == "negative").count()
        neutral_count = await Review.find(Review.sentiment == "neutral").count()
        
        # Count by urgency
        critical_count = await Review.find(Review.urgency_level == "critical").count()
        high_count = await Review.find(Review.urgency_level == "high").count()
        medium_count = await Review.find(Review.urgency_level == "medium").count()
        low_count = await Review.find(Review.urgency_level == "low").count()
        
        # Count emails sent
        emails_sent = await Review.find(Review.email_sent == True).count()
        
        # Count processed reviews
        ai_processed = await Review.find(Review.ai_processed == True).count()
        
        return {
            "total_reviews": total_reviews,
            "sentiment_breakdown": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            },
            "urgency_breakdown": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "emails_sent": emails_sent,
            "ai_processed": ai_processed,
            "processing_rate": (ai_processed / total_reviews * 100) if total_reviews > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to get review stats: {str(e)}")
        return {} 