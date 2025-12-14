"""
Structure Analyzer Service

Orchestrates AI-powered document structure recognition and TOC generation using GPT-4o.
Follows the same pattern as layout_analyzer.py from Story 4.2.
"""

import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.schemas.document_structure import DocumentStructure, TOC, TOCEntry, ChapterMetadata

logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """
    Analyzes document text to detect hierarchical structure and generate TOC.

    Uses GPT-4o with LangChain's .with_structured_output() for strict JSON validation.
    """

    MODEL_NAME = "gpt-4o"

    def __init__(self, api_key: str, temperature: float = 0.0, timeout: int = 60):
        """
        Initialize structure analyzer.

        Args:
            api_key: OpenAI API key
            temperature: Temperature for model (0 = deterministic)
            timeout: Timeout in seconds for API calls (default: 60s for long documents)
        """
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout
        self._client: Optional[ChatOpenAI] = None

    def initialize_client(self) -> ChatOpenAI:
        """
        Initialize ChatOpenAI client with GPT-4o model.

        Returns:
            ChatOpenAI: Configured LangChain chat model

        Raises:
            ValueError: If API key is invalid or missing
            ConnectionError: If client initialization fails
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
            logger.info(f"StructureAnalyzer GPT-4o client initialized (timeout: {self.timeout}s)")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize GPT-4o client for structure analysis: {e}")
            raise ConnectionError(f"Could not initialize GPT-4o client: {e}") from e

    @property
    def client(self) -> ChatOpenAI:
        """Lazy-load AI client on first access."""
        if self._client is None:
            self._client = self.initialize_client()
        return self._client

    async def analyze_structure(
        self,
        text: str,
        language: str,
        page_count: int,
        document_title: Optional[str] = None
    ) -> tuple[DocumentStructure, Dict[str, int]]:
        """
        Analyze document text to detect hierarchical structure and generate TOC.

        Args:
            text: Full extracted text from PDF document
            language: ISO 639-1 language code (e.g., 'en', 'es', 'fr')
            page_count: Total number of pages in document
            document_title: Optional document title (if already detected)

        Returns:
            tuple: (DocumentStructure, token_usage_dict)
                - DocumentStructure: Complete structure with TOC and chapters
                - token_usage_dict: {'prompt': int, 'completion': int} token counts

        Raises:
            TimeoutError: If GPT-4o API call exceeds timeout
            Exception: For other API errors (to be caught by retry/fallback logic)
        """
        logger.info(
            f"Analyzing document structure: {page_count} pages, language={language}, "
            f"text_length={len(text)}"
        )

        # Get structured output client
        structured_client = self.client.with_structured_output(DocumentStructure)

        # Build analysis prompt
        prompt = self._build_structure_prompt(text, language, page_count, document_title)

        # Create message
        message = HumanMessage(content=prompt)

        try:
            # Invoke GPT-4o with structured output
            response = await structured_client.ainvoke([message])
            result: DocumentStructure = response

            # Extract token usage
            token_usage = {"prompt": 0, "completion": 0}

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
                f"Document structure analyzed successfully: "
                f"{result.toc.total_entries} TOC entries, "
                f"{len(result.chapters)} chapters, "
                f"confidence={result.confidence_score}%, "
                f"tokens={token_usage['prompt']}+{token_usage['completion']}"
            )

            # Validate hierarchy
            errors = result.validate_hierarchy()
            if errors:
                logger.warning(f"TOC hierarchy validation found {len(errors)} issues: {errors[:3]}")

            return result, token_usage

        except TimeoutError as e:
            logger.error(f"GPT-4o timeout during structure analysis: {e}")
            raise
        except Exception as e:
            logger.error(f"GPT-4o API error during structure analysis: {e}")
            raise

    def _build_structure_prompt(
        self,
        text: str,
        language: str,
        page_count: int,
        document_title: Optional[str] = None
    ) -> str:
        """
        Build the structure analysis prompt for GPT-4o.

        Args:
            text: Document text to analyze
            language: ISO 639-1 language code
            page_count: Total pages
            document_title: Optional pre-detected title

        Returns:
            Formatted prompt string with few-shot examples
        """
        # Language-specific heading patterns
        language_patterns = self._get_language_patterns(language)

        # Truncate text if too long (keep first 100K chars for context)
        text_sample = text[:100000] if len(text) > 100000 else text
        truncated_note = " [TRUNCATED]" if len(text) > 100000 else ""

        prompt = f"""You are a document structure analysis expert. Analyze the provided document text to identify its hierarchical structure and generate a table of contents.

**Document Information:**
- Pages: {page_count}
- Language: {language}
- Title: {document_title or "Detect from text"}
- Text Length: {len(text)} characters{truncated_note}

**Your Task:**
1. Identify chapter titles, section headers, subsection headers, and sub-subsection headers
2. Determine the hierarchy level (1-4):
   - Level 1 (H1): Main chapters or parts
   - Level 2 (H2): Major sections within chapters
   - Level 3 (H3): Subsections within sections
   - Level 4 (H4): Sub-subsections (finest granularity)
3. Extract page numbers for each heading (estimate based on text position if not explicit)
4. Provide confidence scores (0-100) for each detection based on clarity
5. Detect the document title and author if present
6. Group headings into logical chapters with page ranges

**Language-Specific Patterns ({language}):**
Common heading keywords: {', '.join(language_patterns['chapter'][:5])}
Common section keywords: {', '.join(language_patterns['section'][:5])}

**Pattern Recognition Guidelines:**
- Numbered chapters: "Chapter 1", "1. Introduction", "I. Foundations"
- Numbered sections: "1.1", "1.2.1", "Section A.1"
- Formatting cues: ALL CAPS, Bold text (often indicated by repetition), Larger context
- Standalone lines: Short lines (<80 chars) without trailing punctuation may be headers
- Page breaks: Major sections often start after page breaks

**Quality Guidelines:**
- Assign realistic confidence scores based on:
  - Clear numbering or keywords: 90-100
  - Formatting cues (caps, bold): 80-90
  - Contextual inference: 70-80
  - Uncertain detection: 50-70
- Ensure logical hierarchy: No H3 under H1 without H2
- Provide text samples (first 100 chars after heading) to validate context
- Overall confidence: Your assessment of entire analysis quality (0-100)

**Few-Shot Example 1 - Technical Book:**
```
Input: "CHAPTER 1: INTRODUCTION TO MACHINE LEARNING\\n\\nMachine learning is a subset of artificial intelligence...\\n\\n1.1 What is Machine Learning?\\n\\nIn supervised learning, the algorithm learns from labeled data..."

Output:
{{
  "title": "Introduction to Machine Learning",
  "author": null,
  "language": "en",
  "confidence_score": 92,
  "toc": {{
    "total_entries": 2,
    "max_depth": 2,
    "items": [
      {{"title": "Chapter 1: Introduction to Machine Learning", "level": 1, "page_number": 1, "confidence": 95, "text_sample": "Machine learning is a subset of artificial intelligence...", "type": "chapter"}},
      {{"title": "1.1 What is Machine Learning?", "level": 2, "page_number": 3, "confidence": 92, "text_sample": "In supervised learning, the algorithm learns from labeled data...", "type": "section"}}
    ]
  }},
  "chapters": [
    {{
      "chapter_num": 1,
      "title": "Introduction to Machine Learning",
      "start_page": 1,
      "end_page": 25,
      "subsections": [
        {{"title": "1.1 What is Machine Learning?", "level": 2, "page_number": 3, "confidence": 92, "text_sample": "In supervised learning, the algorithm learns from labeled data...", "type": "section"}}
      ]
    }}
  ]
}}
```

**Few-Shot Example 2 - Academic Paper:**
```
Input: "Abstract\\n\\nThis paper presents a novel approach...\\n\\n1. Introduction\\n\\nRecent advances in deep learning have shown...\\n\\n2. Related Work\\n\\n2.1 Neural Network Architectures\\n\\nConvolutional neural networks..."

Output:
{{
  "title": "Novel Approach to Deep Learning",
  "author": null,
  "language": "en",
  "confidence_score": 88,
  "toc": {{
    "total_entries": 4,
    "max_depth": 2,
    "items": [
      {{"title": "Abstract", "level": 1, "page_number": 1, "confidence": 95, "text_sample": "This paper presents a novel approach...", "type": "chapter"}},
      {{"title": "1. Introduction", "level": 1, "page_number": 2, "confidence": 95, "text_sample": "Recent advances in deep learning have shown...", "type": "chapter"}},
      {{"title": "2. Related Work", "level": 1, "page_number": 5, "confidence": 95, "text_sample": "", "type": "chapter"}},
      {{"title": "2.1 Neural Network Architectures", "level": 2, "page_number": 6, "confidence": 90, "text_sample": "Convolutional neural networks...", "type": "section"}}
    ]
  }},
  "chapters": [
    {{"chapter_num": 1, "title": "Abstract", "start_page": 1, "end_page": 1, "subsections": []}},
    {{"chapter_num": 2, "title": "1. Introduction", "start_page": 2, "end_page": 4, "subsections": []}},
    {{
      "chapter_num": 3,
      "title": "2. Related Work",
      "start_page": 5,
      "end_page": 10,
      "subsections": [
        {{"title": "2.1 Neural Network Architectures", "level": 2, "page_number": 6, "confidence": 90, "text_sample": "Convolutional neural networks...", "type": "section"}}
      ]
    }}
  ]
}}
```

**Document Text to Analyze:**
{text_sample}

**Instructions:**
Analyze the above text carefully and return a complete DocumentStructure JSON matching the schema with:
- Accurate title and author detection
- Complete TOC with all detected headings
- Logical chapter groupings with page ranges
- Realistic confidence scores
- Valid hierarchy (no level jumps)
"""
        return prompt

    def _get_language_patterns(self, language: str) -> Dict[str, list[str]]:
        """
        Get language-specific heading patterns.

        Args:
            language: ISO 639-1 code

        Returns:
            Dictionary with 'chapter' and 'section' pattern lists
        """
        patterns = {
            "en": {
                "chapter": ["Chapter", "CHAPTER", "Part", "PART", "Book", "Appendix"],
                "section": ["Section", "SECTION", "§"],
            },
            "es": {
                "chapter": ["Capítulo", "CAPÍTULO", "Parte", "PARTE", "Libro"],
                "section": ["Sección", "SECCIÓN", "§"],
            },
            "fr": {
                "chapter": ["Chapitre", "CHAPITRE", "Partie", "PARTIE", "Livre"],
                "section": ["Section", "SECTION", "§"],
            },
            "de": {
                "chapter": ["Kapitel", "KAPITEL", "Teil", "TEIL", "Buch"],
                "section": ["Abschnitt", "ABSCHNITT", "§"],
            },
            "zh": {
                "chapter": ["章", "第", "部分", "篇"],
                "section": ["节", "款", "条"],
            },
            "ja": {
                "chapter": ["章", "第", "部", "篇"],
                "section": ["節", "款", "条"],
            },
        }

        # Default to English if language not found
        return patterns.get(language, patterns["en"])
