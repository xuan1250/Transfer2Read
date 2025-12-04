"""
Celery Worker Entrypoint

Imports the Celery app and task modules for worker startup.
Logs worker initialization, LangChain versions, and API key status.
"""
import logging
from app.core.celery_app import celery_app
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log worker startup info
logger.info("=" * 60)
logger.info("Celery Worker Starting - Transfer2Read")
logger.info("=" * 60)

# Log AI SDK availability
try:
    import langchain
    logger.info(f"✓ LangChain loaded successfully (version: {getattr(langchain, '__version__', 'unknown')})")
except ImportError as e:
    logger.error(f"✗ LangChain import failed: {e}")

try:
    import langchain_openai
    version = getattr(langchain_openai, '__version__', 'installed')
    logger.info(f"✓ LangChain OpenAI integration loaded (version: {version})")
except ImportError as e:
    logger.error(f"✗ LangChain OpenAI import failed: {e}")

try:
    import langchain_anthropic
    version = getattr(langchain_anthropic, '__version__', 'installed')
    logger.info(f"✓ LangChain Anthropic integration loaded (version: {version})")
except ImportError as e:
    logger.error(f"✗ LangChain Anthropic import failed: {e}")

# Log API key configuration status
logger.info(f"OpenAI API Key configured: {bool(settings.OPENAI_API_KEY)}")
logger.info(f"Anthropic API Key configured: {bool(settings.ANTHROPIC_API_KEY)}")
logger.info(f"Redis URL: {settings.REDIS_URL}")

logger.info("=" * 60)
logger.info("Worker ready to process tasks")
logger.info("=" * 60)

# This file is imported by Celery CLI: celery -A app.worker worker --loglevel=info
# The celery_app instance is automatically discovered
