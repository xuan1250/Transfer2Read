"""
GPT-4o Provider Implementation

Implements AI layout analysis using OpenAI's GPT-4o model via LangChain.
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.services.ai.base import AIProvider
from app.schemas.layout_analysis import LayoutDetection

logger = logging.getLogger(__name__)


class GPT4Provider(AIProvider):
    """GPT-4o implementation for PDF layout analysis"""

    MODEL_NAME = "gpt-4o"

    def initialize_client(self) -> ChatOpenAI:
        """
        Initialize ChatOpenAI client with GPT-4o model.

        Returns:
            ChatOpenAI: Configured LangChain chat model

        Raises:
            ValueError: If API key is invalid or missing
        """
        if not self.api_key or not self.api_key.startswith("sk-"):
            raise ValueError(
                "Invalid OpenAI API key. Must start with 'sk-'. "
                "Set OPENAI_API_KEY in environment."
            )

        try:
            client = ChatOpenAI(
                model=self.MODEL_NAME,
                api_key=self.api_key,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            logger.info(f"GPT-4o client initialized successfully (timeout: {self.timeout}s)")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize GPT-4o client: {e}")
            raise ConnectionError(f"Could not initialize GPT-4o client: {e}") from e

    async def analyze_page(
        self, image_b64: str, text: str, page_num: int
    ) -> tuple[LayoutDetection, dict]:
        """
        Analyze PDF page using GPT-4o vision and structured output.

        Args:
            image_b64: Base64-encoded image of PDF page
            text: Extracted text layer from page
            page_num: Page number (1-indexed)

        Returns:
            tuple: (LayoutDetection, token_usage_dict)
                - LayoutDetection: Structured analysis with tables, images, equations, layout
                - token_usage_dict: {'prompt': int, 'completion': int} token counts

        Raises:
            TimeoutError: If GPT-4o API call exceeds timeout
            Exception: For other API errors (to be caught by fallback logic)
        """
        logger.info(f"Analyzing page {page_num} with GPT-4o...")

        # Get structured output client
        structured_client = self.client.with_structured_output(LayoutDetection)

        # Create vision message with image and text
        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
                {
                    "type": "text",
                    "text": self._build_analysis_prompt(text, page_num),
                },
            ]
        )

        try:
            # Invoke GPT-4o with structured output
            # Note: We need the raw response to extract token usage
            response = await structured_client.ainvoke([message])
            result: LayoutDetection = response

            # Extract token usage from response metadata if available
            token_usage = {"prompt": 0, "completion": 0}

            # LangChain may expose usage in different ways depending on version
            # Try to extract from the response's additional_kwargs or usage_metadata
            if hasattr(response, 'usage_metadata'):
                token_usage = {
                    "prompt": getattr(response.usage_metadata, 'input_tokens', 0),
                    "completion": getattr(response.usage_metadata, 'output_tokens', 0)
                }
            elif hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                token_usage = {
                    "prompt": usage.get('prompt_tokens', 0),
                    "completion": usage.get('completion_tokens', 0)
                }

            logger.info(
                f"Page {page_num} analyzed successfully: "
                f"{result.tables.count} tables, {result.images.count} images, "
                f"{result.equations.count} equations (confidence: {result.overall_confidence}%), "
                f"tokens: {token_usage['prompt']}+{token_usage['completion']}"
            )

            return result, token_usage

        except TimeoutError as e:
            logger.error(f"GPT-4o timeout on page {page_num}: {e}")
            raise
        except Exception as e:
            logger.error(f"GPT-4o API error on page {page_num}: {e}")
            raise

    def _build_analysis_prompt(self, text: str, page_num: int) -> str:
        """
        Build the analysis prompt for GPT-4o.

        Args:
            text: Extracted text from PDF page
            page_num: Page number being analyzed

        Returns:
            Formatted prompt string
        """
        return f"""You are a PDF analysis expert. Analyze this page image and text to identify complex structural elements.

**Page Number:** {page_num}

**Text Layer:**
{text[:2000]}  # Truncate very long pages

**Task:** Identify and extract:
1. **Tables:** Detect all tables with bounding boxes [x1, y1, x2, y2] in pixels, row/col counts, confidence (0-100), header detection, and content sample
2. **Images:** Detect images/diagrams with bounding boxes, format (photo/diagram/chart), and descriptive alt-text
3. **Equations:** Detect mathematical equations, provide LaTeX representation, confidence, position (inline/block)
4. **Layout:** Determine if multi-column, column count, reflow strategy recommendation
5. **Headers/Footers:** Detect recurring headers/footers with position and text
6. **Language:** Detect primary language (ISO 639-1 code like 'en', 'es', 'fr') and any secondary languages

**Quality Guidelines:**
- Provide precise bounding boxes based on visual analysis
- Assign realistic confidence scores (0-100) based on clarity and detectability
- For tables: Detect headers, estimate rows/cols, provide sample content
- For equations: Convert to valid LaTeX format
- Overall confidence: Your assessment of analysis quality (0-100)

**Output:** Return structured JSON matching the LayoutDetection schema with nested items arrays for tables, images, and equations.
"""

    def get_model_name(self) -> str:
        """Return model name for logging/tracking"""
        return self.MODEL_NAME
