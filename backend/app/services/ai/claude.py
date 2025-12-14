"""
Claude 3.5 Haiku Provider Implementation

Implements AI layout analysis using Anthropic's Claude 3.5 Haiku model via LangChain.
Used as fallback when GPT-4o fails or for cost optimization.
"""

import logging
import base64
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from app.services.ai.base import AIProvider
from app.schemas.layout_analysis import LayoutDetection

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """Claude 3.5 Haiku implementation for PDF layout analysis (fallback)"""

    MODEL_NAME = "claude-3-5-haiku-20241022"

    def initialize_client(self) -> ChatAnthropic:
        """
        Initialize ChatAnthropic client with Claude 3.5 Haiku model.

        Returns:
            ChatAnthropic: Configured LangChain chat model

        Raises:
            ValueError: If API key is invalid or missing
        """
        if not self.api_key or not self.api_key.startswith("sk-ant-"):
            raise ValueError(
                "Invalid Anthropic API key. Must start with 'sk-ant-'. "
                "Set ANTHROPIC_API_KEY in environment."
            )

        try:
            client = ChatAnthropic(
                model=self.MODEL_NAME,
                api_key=self.api_key,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            logger.info(
                f"Claude 3.5 Haiku client initialized successfully (timeout: {self.timeout}s)"
            )
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Claude 3.5 Haiku client: {e}")
            raise ConnectionError(
                f"Could not initialize Claude 3.5 Haiku client: {e}"
            ) from e

    async def analyze_page(
        self, image_b64: str, text: str, page_num: int
    ) -> tuple[LayoutDetection, dict]:
        """
        Analyze PDF page using Claude 3.5 Haiku vision and structured output.

        Args:
            image_b64: Base64-encoded image of PDF page
            text: Extracted text layer from page
            page_num: Page number (1-indexed)

        Returns:
            tuple: (LayoutDetection, token_usage_dict)
                - LayoutDetection: Structured analysis with tables, images, equations, layout
                - token_usage_dict: {'prompt': int, 'completion': int} token counts

        Raises:
            TimeoutError: If Claude API call exceeds timeout
            Exception: For other API errors
        """
        logger.info(f"Analyzing page {page_num} with Claude 3.5 Haiku (fallback)...")

        # Get structured output client
        structured_client = self.client.with_structured_output(LayoutDetection)

        # Create vision message (Claude format)
        message = HumanMessage(
            content=[
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_b64,
                    },
                },
                {
                    "type": "text",
                    "text": self._build_analysis_prompt(text, page_num),
                },
            ]
        )

        try:
            # Invoke Claude with structured output
            response = await structured_client.ainvoke([message])
            result: LayoutDetection = response

            # Extract token usage from response metadata if available
            token_usage = {"prompt": 0, "completion": 0}

            # Try to extract from response metadata (Anthropic format)
            if hasattr(response, 'usage_metadata'):
                token_usage = {
                    "prompt": getattr(response.usage_metadata, 'input_tokens', 0),
                    "completion": getattr(response.usage_metadata, 'output_tokens', 0)
                }
            elif hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('usage', {})
                token_usage = {
                    "prompt": usage.get('input_tokens', 0),
                    "completion": usage.get('output_tokens', 0)
                }

            logger.info(
                f"Page {page_num} analyzed successfully with Claude: "
                f"{result.tables.count} tables, {result.images.count} images, "
                f"{result.equations.count} equations (confidence: {result.overall_confidence}%), "
                f"tokens: {token_usage['prompt']}+{token_usage['completion']}"
            )

            return result, token_usage

        except TimeoutError as e:
            logger.error(f"Claude timeout on page {page_num}: {e}")
            raise
        except Exception as e:
            logger.error(f"Claude API error on page {page_num}: {e}")
            raise

    def _build_analysis_prompt(self, text: str, page_num: int) -> str:
        """
        Build the analysis prompt for Claude 3.5 Haiku (same as GPT-4o).

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
