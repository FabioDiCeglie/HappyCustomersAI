import logging
from typing import Dict, List, Any, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from pydantic import BaseModel
from app.models.review import UrgencyLevel, ReviewCategory
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from app.core.config import settings
from app.services.email_service import send_email


logger = logging.getLogger(__name__)


class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence: float

class IssueCategorizationAnalysis(BaseModel):
    categories: List[str]
    key_issues: List[str]

class UrgencyAnalysis(BaseModel):
    urgency_level: str
    reasoning: str

class GeneratedEmail(BaseModel):
    subject: str
    body: str

class ReviewAnalysisState(TypedDict):
    review_text: str
    customer_name: str
    customer_email: str
    rating: int
    sentiment: str
    sentiment_score: float
    urgency_level: str
    categories: List[str]
    key_issues: List[str]
    should_send_email: bool
    email_sent: bool
    type_of_email_template: str
    analysis_complete: bool
    error: str


_llm_instance: Optional[Any] = None

def get_llm() -> Any:
    """Get or create LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        genai.configure(api_key=settings.google_api_key)
        
        generative_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            client=genai,
            google_api_key=settings.google_api_key,
            temperature=0.1,
        )
        _llm_instance._generative_model = generative_model
    return _llm_instance


def create_review_analysis_graph() -> StateGraph:
    """Create the LangGraph workflow for review analysis"""
    workflow = StateGraph(ReviewAnalysisState)
    
    # Add nodes
    workflow.add_node("analyze_sentiment", analyze_sentiment)
    workflow.add_node("categorize_issues", categorize_issues)
    workflow.add_node("determine_urgency", determine_urgency)
    workflow.add_node("decide_email_action", decide_email_action)
    workflow.add_node("generate_email_content", generate_email_content)
    
    # Define the flow
    workflow.set_entry_point("analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "categorize_issues")
    workflow.add_edge("categorize_issues", "determine_urgency")
    workflow.add_edge("determine_urgency", "decide_email_action")
    
    workflow.add_conditional_edges(
        "decide_email_action",
        should_generate_email,
        {
            "generate_email_content": "generate_email_content",
            END: END
        }
    )
    workflow.add_edge("generate_email_content", END)
    
    return workflow.compile()


def should_generate_email(state: ReviewAnalysisState) -> str:
    """Determine whether to generate an email or end the process."""
    if state.get("should_send_email"):
        return "generate_email_content"
    else:
        return END


async def analyze_sentiment(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Analyze the sentiment of the review"""
    logger.debug(f"🎭 Starting sentiment analysis for customer: {state['customer_name']}")
    
    try:
        parser = PydanticOutputParser(pydantic_object=SentimentAnalysis)
        
        prompt = PromptTemplate(
            template="""You are an expert at analyzing customer review sentiment across all industries and business types.
        
            Analyze the sentiment of the review and provide:
            1. Overall sentiment: positive, negative, or neutral
            2. Confidence score (0.0 to 1.0)
            3. Brief reasoning

            {format_instructions}
            
            Review to analyze:
            Customer: {customer_name}
            Rating: {rating}/5
            Review: {review_text}
            """,
            input_variables=["customer_name", "rating", "review_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        llm = get_llm()
        
        chain = prompt | llm | parser
        
        analysis = await chain.ainvoke({
            "customer_name": state['customer_name'],
            "rating": state.get('rating', 'Not provided'),
            "review_text": state['review_text']
        })
        
        state["sentiment"] = analysis.sentiment
        state["sentiment_score"] = analysis.confidence
        
        logger.info(f"🎭 Sentiment for {state['customer_name']}: {state['sentiment']} ({state['sentiment_score']:.2f})")
        
    except Exception as e:
        logger.error(f"❌ Error analyzing sentiment: {e}")
        state["error"] = f"Sentiment analysis error: {str(e)}"
        state["sentiment"] = "neutral"
        state["sentiment_score"] = 0.0
    
    return state


async def categorize_issues(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Categorize the specific issues mentioned in the review"""
    logger.debug(f"🏷️ Starting issue categorization for customer: {state['customer_name']}")
    
    try:
        categories = [cat.value for cat in ReviewCategory]
        
        parser = PydanticOutputParser(pydantic_object=IssueCategorizationAnalysis)
        
        prompt = PromptTemplate(
            template="""You are an expert at categorizing customer feedback across all industries and business types.
        
        Analyze the review and identify which categories apply. The categories are universal and can apply to any business:
        - quality: Issues with product/service quality, defects, or standards
        - service: Customer service, staff behavior, responsiveness
        - pricing: Cost concerns, value for money, billing issues
        - delivery: Shipping, logistics, timing, fulfillment
        - usability: Ease of use, user interface, accessibility
        - communication: Information clarity, updates, transparency
        - performance: Speed, reliability, functionality, uptime
        - support: Help resources, documentation, technical assistance
        - experience: Overall customer journey, satisfaction, emotions
        - other: Issues that don't fit the above categories

        Available categories: {categories}

        Also extract the key specific issues mentioned.

        {format_instructions}
        
        Review to categorize:
        {review_text}
        Sentiment: {sentiment}
        """,
            input_variables=["categories", "review_text", "sentiment"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        llm = get_llm()
        
        chain = prompt | llm | parser
        
        analysis = await chain.ainvoke({
            "categories": ', '.join(categories),
            "review_text": state['review_text'],
            "sentiment": state['sentiment']
        })
        
        state["categories"] = analysis.categories
        state["key_issues"] = analysis.key_issues
        
        logger.info(f"🏷️ Categorization for {state['customer_name']}: {state['categories']} ({len(state['key_issues'])} issues)")
        
    except Exception as e:
        logger.error(f"❌ Categorization error for customer {state['customer_name']}: {str(e)}")
        state["error"] = f"Categorization error: {str(e)}"
        state["categories"] = ["other"]
        state["key_issues"] = []
    
    return state


async def determine_urgency(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Determine the urgency level of the review"""
    logger.debug(f"🔥 Starting urgency determination for customer: {state['customer_name']}")
    
    try:
        urgency_levels = [level.value for level in UrgencyLevel]
        
        parser = PydanticOutputParser(pydantic_object=UrgencyAnalysis)
        
        prompt = PromptTemplate(
            template="""You are an expert at assessing the urgency of customer feedback across all industries.
        
        Based on the review sentiment, issues, and context, determine the urgency level:
        - critical: Safety concerns, security issues, extremely angry customers, potential legal/PR issues, service outages
        - high: Very unsatisfied customers, multiple serious issues, loss of functionality, demand immediate attention
        - medium: Moderately unsatisfied, specific fixable issues, feature requests, minor bugs
        - low: Minor issues, positive feedback with suggestions, general improvements

        Choose from: {urgency_levels}

        {format_instructions}
        
        Review Analysis:
        Sentiment: {sentiment} (confidence: {sentiment_score})
        Categories: {categories}
        Key Issues: {key_issues}
        Original Review: {review_text}
        """,
            input_variables=["urgency_levels", "sentiment", "sentiment_score", "categories", "key_issues", "review_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        llm = get_llm()
        
        chain = prompt | llm | parser
        
        analysis = await chain.ainvoke({
            "urgency_levels": ', '.join(urgency_levels),
            "sentiment": state['sentiment'],
            "sentiment_score": state['sentiment_score'],
            "categories": ', '.join(state['categories']),
            "key_issues": ', '.join(state['key_issues']),
            "review_text": state['review_text']
        })
        
        state["urgency_level"] = analysis.urgency_level
        
        logger.info(f"🔥 Urgency for {state['customer_name']}: {state['urgency_level']}")
        
    except Exception as e:
        logger.error(f"❌ Urgency determination error for customer {state['customer_name']}: {str(e)}")
        state["error"] = f"Urgency determination error: {str(e)}"
        state["urgency_level"] = "medium"
    
    return state


async def decide_email_action(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Decide whether to send an email and which template to use"""
    logger.debug(f"🤔 Deciding email action for {state['customer_name']}")
    try:
        # Only send emails for negative reviews with medium+ urgency
        should_send = (
            state["sentiment"] == "negative" and
            state["urgency_level"] in ["medium", "high", "critical"]
        )
        
        state["should_send_email"] = should_send
        
        if should_send:
            # Determine email template based on categories and urgency
            if state["urgency_level"] == "critical":
                state["type_of_email_template"] = "critical_response"
            elif "quality" in state["categories"]:
                state["type_of_email_template"] = "quality_concern"
            elif "service" in state["categories"]:
                state["type_of_email_template"] = "service_concern"
            elif "delivery" in state["categories"]:
                state["type_of_email_template"] = "delivery_concern"
            elif "support" in state["categories"]:
                state["type_of_email_template"] = "support_concern"
            else:
                state["type_of_email_template"] = "general_concern"
            logger.info(f"✅ Email will be sent to {state['customer_name']} (template: {state['type_of_email_template']})")
        else:
            state["type_of_email_template"] = None
            state["analysis_complete"] = True
            logger.info(f"📪 Email not required for {state['customer_name']}. Conditions not met.")
        
    except Exception as e:
        logger.error(f"❌ Email decision error for customer {state['customer_name']}: {str(e)}")
        state["error"] = f"Email decision error: {str(e)}"
    
    return state


async def generate_email_content(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Generate a personalized email response based on the analysis."""
    logger.debug(f"📧 Starting email generation for customer: {state['customer_name']}")

    try:
        parser = PydanticOutputParser(pydantic_object=GeneratedEmail)

        prompt = PromptTemplate(
            template="""You are a world-class customer support agent responsible for writing personalized, empathetic, and professional emails to customers based on their feedback.

            **Context:**
            - Customer Name: {customer_name}
            - Service Name: {service_name}
            - Service Email: {service_email}
            - Review Sentiment: {sentiment}
            - Urgency: {urgency_level}
            - Key Issues Identified: {key_issues}
            - Original Review: {review_text}

            **Your Task:**
            Generate a complete email (subject and body) to send to the customer. The tone and content should be guided by the "Response Type".

            **Response Type:** {response_type}

            **Guidelines for Different Response Types:**

            *   **critical_response**:
                *   Acknowledge the severity of the issue immediately.
                *   Express deep concern.
                *   Offer immediate actions like a call with a manager, a full refund, and a complimentary return visit.
                *   Keep it concise and action-oriented.
                *   Example tone: "We are deeply concerned about your recent experience..."

            *   **quality_concern**:
                *   Apologize for not meeting quality standards.
                *   Mention that feedback has been shared with the quality team.
                *   Outline steps being taken (e.g., process review).
                *   Offer a complimentary return experience to demonstrate improvement.
                *   Example tone: "We sincerely apologize that our quality did not meet your expectations."

            *   **service_concern**:
                *   Apologize for the service lapse.
                *   Mention that feedback has been discussed with the service team and extra training is being implemented.
                *   Offer a complimentary service on the next visit to make it right.
                *   Example tone: "We are sorry to hear that our service did not meet your expectations."
            
            *   **general_concern**:
                *   Thank the customer for their feedback.
                *   Acknowledge their concerns and state that they have been shared with management.
                *   Reassure them that you are taking steps to improve.
                *   Invite them back to experience the improvements.
                *   Example tone: "Thank you for sharing your feedback about your experience..."
            
            *   **delivery_concern**:
                *   Apologize for delivery issues.
                *   Mention that you've reviewed the issue with logistics.
                *   Offer a delivery credit or priority handling for the next order.
                *   Example tone: "We sincerely apologize for the delivery issues you experienced."

            *   **support_concern**:
                *   Apologize for the support experience.
                *   Mention that support training and processes are being improved.
                *   Encourage them to contact support again for proper assistance.
                *   Example tone: "Thank you for your feedback regarding your support experience."

            **Final Output Instructions:**
            - Write the email body in plain text, not markdown.
            - Ensure the tone is appropriate for the situation.
            - Personalize the email using the customer's name and the specific issues they raised.
            - Sign off with the "{service_name}".

            {format_instructions}
            """,
            input_variables=[
                "customer_name", "service_name", "service_email",
                "sentiment", "urgency_level", "key_issues", "review_text",
                "response_type"
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        llm = get_llm()
        chain = prompt | llm | parser

        analysis = await chain.ainvoke({
            "customer_name": state['customer_name'],
            "service_name": settings.from_name,
            "service_email": settings.from_email,
            "sentiment": state['sentiment'],
            "urgency_level": state['urgency_level'],
            "key_issues": '\n- '.join(state['key_issues']),
            "review_text": state['review_text'],
            "response_type": state['type_of_email_template']
        })

        logger.info(f"✅ Email content generated for {state['customer_name']}")

        email_sent_successfully = await send_email(
            to_email=state['customer_email'],
            subject=analysis.subject,
            body=analysis.body
        )
        state['email_sent'] = email_sent_successfully

    except Exception as e:
        logger.error(f"❌ Email generation error for customer {state['customer_name']}: {str(e)}")
        state["error"] = f"Email generation error: {str(e)}"
        state['email_sent'] = False

    state["analysis_complete"] = True
    return state


# Global graph instance for reuse
_graph_instance: Optional[StateGraph] = None


def get_review_analysis_graph() -> StateGraph:
    """Get or create the review analysis graph"""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_review_analysis_graph()
    return _graph_instance


async def analyze_review(
    review_text: str, 
    customer_name: str, 
    customer_email: str,
    rating: int = None
) -> Dict[str, Any]:
    """Analyze a review and return the complete analysis"""
    
    logger.info(f"🚀 Analyzing review for: {customer_name}")
    
    initial_state = ReviewAnalysisState(
        review_text=review_text,
        customer_name=customer_name,
        customer_email=customer_email,
        rating=rating or 0,
        sentiment="",
        sentiment_score=0.0,
        urgency_level="",
        categories=[],
        key_issues=[],
        should_send_email=False,
        email_sent=False,
        type_of_email_template="",
        analysis_complete=False,
        error=""
    )
    
    graph = get_review_analysis_graph()
    result = await graph.ainvoke(initial_state)
    
    logger.info(f"🎉 Analysis complete for {customer_name}: Sentiment={result['sentiment']}, Urgency={result['urgency_level']}, EmailSent={result['email_sent']}")
    
    return {
        "sentiment": result["sentiment"],
        "sentiment_score": result["sentiment_score"],
        "urgency_level": result["urgency_level"],
        "categories": result["categories"],
        "key_issues": result["key_issues"],
        "should_send_email": result["should_send_email"],
        "email_sent": result["email_sent"],
        "type_of_email_template": result["type_of_email_template"],
        "analysis_complete": result["analysis_complete"],
        "error": result.get("error", "")
    }