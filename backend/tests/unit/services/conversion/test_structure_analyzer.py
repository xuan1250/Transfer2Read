"""
Unit Tests for Structure Analyzer

Tests AI-powered document structure recognition with mocked GPT-4o responses.
All tests use fixtures to avoid API costs (zero cost testing).
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from app.services.ai.structure_analyzer import StructureAnalyzer
from app.schemas.document_structure import DocumentStructure, TOC, TOCEntry


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_document_structure():
    """Sample DocumentStructure response from GPT-4o"""
    return {
        "title": "Introduction to Machine Learning",
        "author": "Dr. Jane Smith",
        "language": "en",
        "confidence_score": 92,
        "toc": {
            "total_entries": 3,
            "max_depth": 2,
            "items": [
                {
                    "title": "Chapter 1: Foundations",
                    "level": 1,
                    "page_number": 5,
                    "confidence": 95,
                    "text_sample": "This chapter introduces the basic concepts of machine learning and its applications.",
                    "type": "chapter"
                },
                {
                    "title": "1.1 What is Machine Learning?",
                    "level": 2,
                    "page_number": 6,
                    "confidence": 92,
                    "text_sample": "Machine learning is a subset of artificial intelligence that enables systems to learn.",
                    "type": "section"
                },
                {
                    "title": "1.2 Applications",
                    "level": 2,
                    "page_number": 10,
                    "confidence": 90,
                    "text_sample": "ML is used in various domains including computer vision, natural language processing.",
                    "type": "section"
                }
            ]
        },
        "chapters": [
            {
                "chapter_num": 1,
                "title": "Foundations",
                "start_page": 5,
                "end_page": 24,
                "subsections": [
                    {
                        "title": "1.1 What is Machine Learning?",
                        "level": 2,
                        "page_number": 6,
                        "confidence": 92,
                        "text_sample": "Machine learning is a subset of artificial intelligence.",
                        "type": "section"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def analyzer():
    """Create StructureAnalyzer instance with test API key"""
    return StructureAnalyzer(api_key="sk-test-key", temperature=0.0, timeout=30)


# ============================================================================
# Initialization Tests
# ============================================================================

def test_analyzer_initialization(analyzer):
    """Test StructureAnalyzer initializes correctly"""
    assert analyzer.api_key == "sk-test-key"
    assert analyzer.temperature == 0.0
    assert analyzer.timeout == 30
    assert analyzer._client is None  # Lazy-loaded


def test_analyzer_initialization_invalid_api_key():
    """Test StructureAnalyzer raises error for invalid API key"""
    analyzer = StructureAnalyzer(api_key="invalid-key", timeout=30)

    with pytest.raises(ValueError, match="Invalid OpenAI API key"):
        _ = analyzer.client  # Trigger lazy initialization


# ============================================================================
# Structure Analysis Tests
# ============================================================================

@pytest.mark.asyncio
async def test_analyze_structure_success(analyzer, sample_document_structure):
    """Test successful structure analysis with mocked GPT-4o response"""

    # Mock the LangChain ChatOpenAI client
    mock_client = Mock()
    mock_structured_client = Mock()

    # Create mock response with Pydantic model
    mock_response = DocumentStructure(**sample_document_structure)
    mock_response.usage_metadata = Mock(input_tokens=850, output_tokens=320)

    # Mock ainvoke to return DocumentStructure
    mock_structured_client.ainvoke = AsyncMock(return_value=mock_response)
    mock_client.with_structured_output = Mock(return_value=mock_structured_client)

    analyzer._client = mock_client

    # Run analysis
    result, token_usage = await analyzer.analyze_structure(
        text="Sample document text with Chapter 1 and sections...",
        language="en",
        page_count=50,
        document_title=None
    )

    # Assertions
    assert isinstance(result, DocumentStructure)
    assert result.title == "Introduction to Machine Learning"
    assert result.toc.total_entries == 3
    assert result.toc.max_depth == 2
    assert len(result.chapters) == 1
    assert result.confidence_score == 92

    assert token_usage["prompt"] == 850
    assert token_usage["completion"] == 320

    # Verify prompt was built correctly
    mock_structured_client.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_structure_timeout(analyzer):
    """Test structure analysis handles timeout gracefully"""

    mock_client = Mock()
    mock_structured_client = Mock()
    mock_structured_client.ainvoke = AsyncMock(side_effect=TimeoutError("GPT-4o timeout"))
    mock_client.with_structured_output = Mock(return_value=mock_structured_client)

    analyzer._client = mock_client

    with pytest.raises(TimeoutError, match="GPT-4o timeout"):
        await analyzer.analyze_structure(
            text="Sample text",
            language="en",
            page_count=10
        )


@pytest.mark.asyncio
async def test_analyze_structure_api_error(analyzer):
    """Test structure analysis handles API errors"""

    mock_client = Mock()
    mock_structured_client = Mock()
    mock_structured_client.ainvoke = AsyncMock(side_effect=Exception("API rate limit exceeded"))
    mock_client.with_structured_output = Mock(return_value=mock_structured_client)

    analyzer._client = mock_client

    with pytest.raises(Exception, match="API rate limit exceeded"):
        await analyzer.analyze_structure(
            text="Sample text",
            language="en",
            page_count=10
        )


# ============================================================================
# Hierarchy Validation Tests
# ============================================================================

def test_validate_hierarchy_valid(sample_document_structure):
    """Test hierarchy validation passes for valid structure"""
    doc_struct = DocumentStructure(**sample_document_structure)
    errors = doc_struct.validate_hierarchy()
    assert len(errors) == 0


def test_validate_hierarchy_invalid_jump():
    """Test hierarchy validation detects invalid level jumps (H1 -> H3)"""
    invalid_structure = {
        "title": "Test Document",
        "author": None,
        "language": "en",
        "confidence_score": 80,
        "toc": {
            "total_entries": 2,
            "max_depth": 3,
            "items": [
                {
                    "title": "Chapter 1",
                    "level": 1,
                    "page_number": 1,
                    "confidence": 90,
                    "text_sample": "Introduction text",
                    "type": "chapter"
                },
                {
                    "title": "1.1.1 Deep Section",  # Invalid jump from H1 to H3
                    "level": 3,
                    "page_number": 5,
                    "confidence": 85,
                    "text_sample": "Deep section text",
                    "type": "subsection"
                }
            ]
        },
        "chapters": []
    }

    doc_struct = DocumentStructure(**invalid_structure)
    errors = doc_struct.validate_hierarchy()

    assert len(errors) == 1
    assert "Invalid level jump from H1 to H3" in errors[0]


# ============================================================================
# Language Pattern Tests
# ============================================================================

def test_get_language_patterns_english(analyzer):
    """Test language patterns for English"""
    patterns = analyzer._get_language_patterns("en")

    assert "Chapter" in patterns["chapter"]
    assert "Section" in patterns["section"]


def test_get_language_patterns_spanish(analyzer):
    """Test language patterns for Spanish"""
    patterns = analyzer._get_language_patterns("es")

    assert "Capítulo" in patterns["chapter"]
    assert "Sección" in patterns["section"]


def test_get_language_patterns_french(analyzer):
    """Test language patterns for French"""
    patterns = analyzer._get_language_patterns("fr")

    assert "Chapitre" in patterns["chapter"]
    assert "Section" in patterns["section"]


def test_get_language_patterns_unsupported_defaults_to_english(analyzer):
    """Test unsupported language defaults to English patterns"""
    patterns = analyzer._get_language_patterns("xx")  # Invalid language code

    assert "Chapter" in patterns["chapter"]  # Default to English


# ============================================================================
# Prompt Building Tests
# ============================================================================

def test_build_structure_prompt_includes_language_patterns(analyzer):
    """Test prompt includes language-specific patterns"""
    prompt = analyzer._build_structure_prompt(
        text="Sample document text",
        language="es",
        page_count=10,
        document_title="Manual Técnico"
    )

    assert "Capítulo" in prompt
    assert "Sección" in prompt
    assert "Manual Técnico" in prompt
    assert "es" in prompt


def test_build_structure_prompt_truncates_long_text(analyzer):
    """Test prompt truncates very long documents"""
    long_text = "A" * 200000  # 200K characters

    prompt = analyzer._build_structure_prompt(
        text=long_text,
        language="en",
        page_count=300
    )

    # Prompt should include truncation note
    assert "[TRUNCATED]" in prompt
    # Prompt should be truncated to ~100K chars
    assert len(prompt) < 120000


# ============================================================================
# Pydantic Schema Tests
# ============================================================================

def test_document_structure_schema_validation():
    """Test DocumentStructure Pydantic schema validates correctly"""
    valid_data = {
        "title": "Test Document",
        "author": "John Doe",
        "language": "en",
        "confidence_score": 85,
        "toc": {
            "total_entries": 1,
            "max_depth": 1,
            "items": [
                {
                    "title": "Chapter 1",
                    "level": 1,
                    "page_number": 1,
                    "confidence": 90,
                    "text_sample": "Sample text",
                    "type": "chapter"
                }
            ]
        },
        "chapters": []
    }

    doc_struct = DocumentStructure(**valid_data)
    assert doc_struct.title == "Test Document"
    assert doc_struct.confidence_score == 85


def test_toc_entry_text_sample_truncation():
    """Test TOCEntry truncates text_sample to 100 characters"""
    long_sample = "A" * 200

    entry = TOCEntry(
        title="Test Entry",
        level=1,
        page_number=1,
        confidence=90,
        text_sample=long_sample,
        type="chapter"
    )

    assert len(entry.text_sample) == 100
    assert entry.text_sample == "A" * 100
