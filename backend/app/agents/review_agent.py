import logging
from typing import Dict, List, Any, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from pydantic import BaseModel, Field
from app.models.review import UrgencyLevel, ReviewCategory
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from app.core.config import settings

# Set up logger
logger = logging.getLogger(__name__)


# Pydantic models for structured outputs
class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence: float

class IssueCategorizationAnalysis(BaseModel):
    categories: List[str]
    key_issues: List[str]


class UrgencyAnalysis(BaseModel):
    urgency_level: str
    reasoning: str


class ReviewAnalysisState(TypedDict):
    review_text: str
    customer_name: str
    rating: int
    sentiment: str
    sentiment_score: float
    urgency_level: str
    categories: List[str]
    key_issues: List[str]
    should_send_email: bool
    email_template: str
    analysis_complete: bool
    error: str


# Global LLM instance for reuse
_llm_instance: Optional[Any] = None

def get_llm() -> Any:
    """Get or create LLM instance"""
    global _llm_instance
    if _llm_instance is None:
        # Configure the Google Generative AI client
        genai.configure(api_key=settings.google_api_key)
        
        # Create the client (GenerativeModel instance)
        generative_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            client=genai,
            google_api_key=settings.google_api_key,
            temperature=0.1,
        )
        # Manually set the generative model
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
    
    # Define the flow
    workflow.set_entry_point("analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "categorize_issues")
    workflow.add_edge("categorize_issues", "determine_urgency")
    workflow.add_edge("determine_urgency", "decide_email_action")
    workflow.add_edge("decide_email_action", END)
    
    return workflow.compile()


async def analyze_sentiment(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Analyze the sentiment of the review"""
    logger.info(f"Starting sentiment analysis for customer: {state['customer_name']}")
    
    try:
        # Set up the parser
        parser = PydanticOutputParser(pydantic_object=SentimentAnalysis)
        
        # Create the prompt template
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
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Invoke the chain
        analysis = await chain.ainvoke({
            "customer_name": state['customer_name'],
            "rating": state.get('rating', 'Not provided'),
            "review_text": state['review_text']
        })
        
        state["sentiment"] = analysis.sentiment
        state["sentiment_score"] = analysis.confidence
        
        logger.info(f"Sentiment analysis completed - Sentiment: {state['sentiment']}, Score: {state['sentiment_score']}")
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        state["error"] = f"Sentiment analysis error: {str(e)}"
        state["sentiment"] = "neutral"
        state["sentiment_score"] = 0.0
    
    return state


async def categorize_issues(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Categorize the specific issues mentioned in the review"""
    logger.info(f"Starting issue categorization for customer: {state['customer_name']}")
    
    try:
        categories = [cat.value for cat in ReviewCategory]
        
        # Set up the parser
        parser = PydanticOutputParser(pydantic_object=IssueCategorizationAnalysis)
        
        # Create the prompt template
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
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Invoke the chain
        analysis = await chain.ainvoke({
            "categories": ', '.join(categories),
            "review_text": state['review_text'],
            "sentiment": state['sentiment']
        })
        
        state["categories"] = analysis.categories
        state["key_issues"] = analysis.key_issues
        
        logger.info(f"Issue categorization completed - Categories: {state['categories']}, Key issues: {len(state['key_issues'])} identified")
        
    except Exception as e:
        logger.error(f"Categorization error for customer {state['customer_name']}: {str(e)}")
        state["error"] = f"Categorization error: {str(e)}"
        state["categories"] = ["other"]
        state["key_issues"] = []
    
    return state


async def determine_urgency(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Determine the urgency level of the review"""
    logger.info(f"Starting urgency determination for customer: {state['customer_name']}")
    
    try:
        urgency_levels = [level.value for level in UrgencyLevel]
        
        # Set up the parser
        parser = PydanticOutputParser(pydantic_object=UrgencyAnalysis)
        
        # Create the prompt template
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
        
        # Create the chain
        chain = prompt | llm | parser
        
        # Invoke the chain
        analysis = await chain.ainvoke({
            "urgency_levels": ', '.join(urgency_levels),
            "sentiment": state['sentiment'],
            "sentiment_score": state['sentiment_score'],
            "categories": ', '.join(state['categories']),
            "key_issues": ', '.join(state['key_issues']),
            "review_text": state['review_text']
        })
        
        state["urgency_level"] = analysis.urgency_level
        
        logger.info(f"Urgency determination completed - Urgency level: {state['urgency_level']}")
        
    except Exception as e:
        logger.error(f"Urgency determination error for customer {state['customer_name']}: {str(e)}")
        state["error"] = f"Urgency determination error: {str(e)}"
        state["urgency_level"] = "medium"
    
    return state


async def decide_email_action(state: ReviewAnalysisState) -> ReviewAnalysisState:
    """Decide whether to send an email and which template to use"""
    try:
        # Only send emails for negative reviews or medium+ urgency
        should_send = (
            state["sentiment"] == "negative" or 
            state["urgency_level"] in ["medium", "high", "critical"]
        )
        
        state["should_send_email"] = should_send
        
        if should_send:
            # Determine email template based on categories and urgency
            if state["urgency_level"] == "critical":
                state["email_template"] = "critical_response"
            elif "quality" in state["categories"]:
                state["email_template"] = "quality_concern"
            elif "service" in state["categories"]:
                state["email_template"] = "service_concern"
            elif "delivery" in state["categories"]:
                state["email_template"] = "delivery_concern"
            elif "support" in state["categories"]:
                state["email_template"] = "support_concern"
            else:
                state["email_template"] = "general_concern"
        else:
            state["email_template"] = None
        
        state["analysis_complete"] = True
        
    except Exception as e:
        state["error"] = f"Email decision error: {str(e)}"
        state["should_send_email"] = False
        state["email_template"] = None
    
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
    rating: int = None
) -> Dict[str, Any]:
    """Analyze a review and return the complete analysis"""
    
    logger.info(f"Starting complete review analysis for customer: {customer_name}")
    
    initial_state = ReviewAnalysisState(
        review_text=review_text,
        customer_name=customer_name,
        rating=rating or 0,
        sentiment="",
        sentiment_score=0.0,
        urgency_level="",
        categories=[],
        key_issues=[],
        should_send_email=False,
        email_template="",
        analysis_complete=False,
        error=""
    )
    
    graph = get_review_analysis_graph()
    result = await graph.ainvoke(initial_state)
    
    logger.info(f"Review analysis completed for customer: {customer_name} - Sentiment: {result['sentiment']}, Urgency: {result['urgency_level']}, Email needed: {result['should_send_email']}")
    
    return {
        "sentiment": result["sentiment"],
        "sentiment_score": result["sentiment_score"],
        "urgency_level": result["urgency_level"],
        "categories": result["categories"],
        "key_issues": result["key_issues"],
        "should_send_email": result["should_send_email"],
        "email_template": result["email_template"],
        "analysis_complete": result["analysis_complete"],
        "error": result.get("error", "")
    }