"""
AI Test Tasks

Celery tasks for testing AI connectivity with OpenAI (GPT-4o) and
Anthropic (Claude 3 Haiku) via LangChain.
"""
import logging
from celery import Task
from typing import Literal
from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="test_ai_connection")
def test_ai_connection(
    self: Task, 
    provider: Literal["openai", "anthropic"] = "openai"
) -> dict:
    """
    Test AI API connectivity using LangChain.
    
    Args:
        provider: AI provider to test ("openai" or "anthropic")
        
    Returns:
        dict with status and response from AI model
        
    Raises:
        Retries on API failures with exponential backoff
    """
    try:
        logger.info(f"Testing {provider} AI connection...")
        
        if provider == "openai":
            # Test OpenAI GPT-4o connection
            from langchain_openai import ChatOpenAI
            
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            
            logger.info("Initializing ChatOpenAI (GPT-4o)...")
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                api_key=settings.OPENAI_API_KEY,
                timeout=30
            )
            
            logger.info("Sending test prompt to GPT-4o...")
            response = llm.invoke("Respond with 'AI connection successful'")
            
            result = {
                "status": "success",
                "provider": "openai",
                "model": "gpt-4o",
                "response": response.content,
                "metadata": {
                    "token_usage": getattr(response, "usage_metadata", None)
                }
            }
            logger.info(f"OpenAI test successful: {result['response']}")
            return result
            
        elif provider == "anthropic":
            # Test Anthropic Claude 3 Haiku connection
            from langchain_anthropic import ChatAnthropic
            
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            
            logger.info("Initializing ChatAnthropic (Claude 3 Haiku)...")
            llm = ChatAnthropic(
                model="claude-3-haiku-20240307",
                temperature=0,
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=30
            )
            
            logger.info("Sending test prompt to Claude 3 Haiku...")
            response = llm.invoke("Respond with 'AI connection successful'")
            
            result = {
                "status": "success",
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "response": response.content
            }
            logger.info(f"Anthropic test successful: {result['response']}")
            return result
            
        else:
            raise ValueError(f"Invalid provider: {provider}. Must be 'openai' or 'anthropic'")
            
    except Exception as exc:
        logger.error(f"AI connection test failed: {exc}", exc_info=True)
        
        # Retry with exponential backoff: 1min, 5min, 15min
        retry_delays = [60, 300, 900]
        retry_count = self.request.retries
        countdown = retry_delays[min(retry_count, len(retry_delays) - 1)]
        
        # Raise to trigger retry
        raise self.retry(exc=exc, countdown=countdown)
