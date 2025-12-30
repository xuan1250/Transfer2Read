"""
Abstract Base Class for AI Providers

Defines the interface that all AI providers (GPT-4o, Claude) must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.layout_analysis import LayoutDetection


class AIProvider(ABC):
    """Abstract base class for AI layout analysis providers"""

    def __init__(self, api_key: str, temperature: float = 0.0, timeout: int = 30):
        """
        Initialize AI provider.

        Args:
            api_key: API key for the AI service
            temperature: Temperature for model (0 = deterministic)
            timeout: Timeout in seconds for API calls
        """
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout
        self._client = None

    @abstractmethod
    def initialize_client(self) -> Any:
        """
        Initialize the AI client (LangChain ChatModel).

        Returns:
            Initialized LangChain chat model instance

        Raises:
            ValueError: If API key is invalid
            ConnectionError: If client initialization fails
        """
        pass

    @abstractmethod
    async def analyze_page(
        self, image_b64: str, text: str, page_num: int
    ) -> LayoutDetection:
        """
        Analyze a single PDF page using AI vision and text.

        Args:
            image_b64: Base64-encoded page image for vision analysis
            text: Extracted text layer from PDF page
            page_num: Page number (1-indexed)

        Returns:
            LayoutDetection: Structured layout analysis result

        Raises:
            TimeoutError: If API call exceeds timeout
            APIError: If AI service returns an error
            ValidationError: If response doesn't match schema
        """
        pass

    @property
    def client(self):
        """
        Lazy-load AI client on first access.

        Returns:
            Initialized AI client
        """
        if self._client is None:
            self._client = self.initialize_client()
        return self._client

    def get_model_name(self) -> str:
        """
        Get the name of the AI model being used.

        Returns:
            Model name (e.g., "gpt-4o", "claude-3-5-haiku-20241022")
        """
        return self.__class__.__name__

    async def aclose(self) -> None:
        """
        Cleanup AI client resources asynchronously.

        Subclasses should override to properly close httpx clients and other async resources.
        Must be called before closing the event loop to prevent 'Event loop is closed' errors.
        """
        if self._client is not None:
            # LangChain clients may have internal httpx AsyncClient
            # Delete reference to allow proper garbage collection
            self._client = None
