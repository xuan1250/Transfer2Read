"""
Test basic EPUB generation functionality.

This test verifies that the EpubGenerator can create a minimal valid EPUB file.
"""
import pytest
from pathlib import Path
import tempfile
from io import BytesIO

from app.services.conversion.epub_generator import EpubGenerator
from app.services.conversion.font_manager import FontManager
from app.services.conversion.epub_validator import EpubValidator
from app.schemas.document_structure import DocumentStructure, TOC, ChapterMetadata, TOCEntry


def test_epub_basic_creation():
    """Test basic EPUB creation with minimal metadata."""
    # Create generator
    generator = EpubGenerator(job_id="test_job_123", user_id="test_user")

    # Create book
    book = generator.create_epub_book()
    assert book is not None
    assert generator.book is not None

    # Set metadata
    generator.set_metadata(
        title="Test Document",
        author="Test Author",
        language="en"
    )

    assert generator.book.title == "Test Document"
    assert len(generator.book.get_metadata('DC', 'creator')) > 0

    # Verify identifier is set
    identifier = generator.book.get_metadata('DC', 'identifier')
    assert len(identifier) > 0


def test_epub_metadata_extraction():
    """Test PDF metadata extraction (with empty PDF)."""
    generator = EpubGenerator(job_id="test_job_123", user_id="test_user")

    # Create minimal PDF bytes (this will fail gracefully)
    metadata = generator._extract_pdf_metadata(b"")
    assert isinstance(metadata, dict)
    # Empty or invalid PDF returns empty dict


def test_epub_write_to_bytes():
    """Test writing EPUB to bytes."""
    from ebooklib import epub as epub_lib

    generator = EpubGenerator(job_id="test_job_123", user_id="test_user")
    generator.create_epub_book()
    generator.set_metadata(title="Test", author="Author")

    # Add minimal chapter
    chapter = epub_lib.EpubHtml(title='Chapter 1', file_name='chap_1.xhtml', lang='en')
    chapter.content = '<html><body><h1>Chapter 1</h1><p>Test content</p></body></html>'
    generator.book.add_item(chapter)

    # Set spine and navigation
    generator.book.spine = ['nav', chapter]
    generator.book.toc = (epub_lib.Link('chap_1.xhtml', 'Chapter 1', 'ch1'),)
    generator.book.add_item(epub_lib.EpubNcx())
    generator.book.add_item(epub_lib.EpubNav())

    # Write to bytes
    epub_bytes = generator._write_epub_to_bytes()

    assert isinstance(epub_bytes, bytes)
    assert len(epub_bytes) > 0
    # EPUB files are ZIP files, should start with PK
    assert epub_bytes[:2] == b'PK'


def test_font_manager_detection():
    """Test font detection for different languages."""
    font_manager = FontManager()

    # Test Chinese detection
    zh_fonts = font_manager.detect_required_fonts('zh', '这是中文测试')
    assert 'noto-sans-sc' in zh_fonts

    # Test Japanese detection
    ja_fonts = font_manager.detect_required_fonts('ja', 'これは日本語のテストです')
    assert 'noto-sans-jp' in ja_fonts

    # Test Korean detection
    ko_fonts = font_manager.detect_required_fonts('ko', '이것은 한국어 테스트입니다')
    assert 'noto-sans-kr' in ko_fonts

    # Test English (no special fonts)
    en_fonts = font_manager.detect_required_fonts('en', 'This is English')
    assert len(en_fonts) == 0


def test_font_face_css_generation():
    """Test CSS @font-face rule generation."""
    font_manager = FontManager()

    css = font_manager.generate_font_face_css(['noto-sans-sc', 'noto-sans-jp'])

    assert '@font-face' in css
    assert 'Noto Sans SC' in css
    assert 'Noto Sans JP' in css
    assert 'font/woff2' in css or '../fonts/' in css


def test_image_compression_validator():
    """Test image compression in EPUB validator."""
    from PIL import Image

    validator = EpubValidator()

    # Create a test image (PNG)
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    png_bytes = img_buffer.getvalue()

    # Compress image
    compressed_bytes, saved = validator._compress_image(png_bytes, quality=85)

    assert isinstance(compressed_bytes, bytes)
    assert len(compressed_bytes) > 0
    # Compression may or may not reduce size depending on image complexity


def test_image_file_detection():
    """Test image file type detection."""
    validator = EpubValidator()

    assert validator._is_compressible_image('images/cover.png') is True
    assert validator._is_compressible_image('images/photo.jpg') is True
    assert validator._is_compressible_image('images/photo.jpeg') is True
    assert validator._is_compressible_image('styles/style.css') is False
    assert validator._is_compressible_image('content.xhtml') is False


def test_epub_size_validation():
    """Test EPUB file size validation."""
    validator = EpubValidator()

    # Test within limits
    is_ok, msg = validator.check_file_size(
        epub_size_bytes=100_000,  # 100 KB
        pdf_size_bytes=100_000,   # 100 KB
        max_ratio=1.2
    )
    assert is_ok is True

    # Test oversized
    is_ok, msg = validator.check_file_size(
        epub_size_bytes=150_000,  # 150 KB
        pdf_size_bytes=100_000,   # 100 KB
        max_ratio=1.2
    )
    assert is_ok is False
    assert 'oversized' in msg.lower()


def test_epub_full_generation():
    """Test full EPUB generation with HTML content."""
    generator = EpubGenerator(job_id="test_job_full", user_id="test_user")
    
    # Mock inputs
    structure = DocumentStructure(
        title="Full Test",
        author="Tester",
        language="en",
        chapters=[
            ChapterMetadata(title="Chapter 1", start_page=1, end_page=1, chapter_num=1)
        ],
        toc={"items": [], "total_entries": 0, "max_depth": 1},
        confidence_score=100
    )
    html_content = "<html><body><div class='page'><h1>Chapter 1</h1><p>Content</p></div></body></html>"
    pdf_bytes = b"%PDF-1.4..."  # Dummy PDF
    
    # Generate
    epub_bytes, metadata = generator.generate(
        document_structure=structure,
        html_content=html_content,
        pdf_bytes=pdf_bytes
    )
    
    assert iter(epub_bytes)
    assert len(epub_bytes) > 0
    assert metadata['title'] == "Full Test"
    assert metadata['chapter_count'] == 1


if __name__ == "__main__":
    # Run tests
    test_epub_basic_creation()
    print("✓ test_epub_basic_creation passed")

    test_epub_metadata_extraction()
    print("✓ test_epub_metadata_extraction passed")

    test_epub_write_to_bytes()
    print("✓ test_epub_write_to_bytes passed")

    test_font_manager_detection()
    print("✓ test_font_manager_detection passed")

    test_font_face_css_generation()
    print("✓ test_font_face_css_generation passed")

    test_image_compression_validator()
    print("✓ test_image_compression_validator passed")

    test_image_file_detection()
    print("✓ test_image_file_detection passed")

    test_epub_size_validation()
    print("✓ test_epub_size_validation passed")

    test_epub_full_generation()
    print("✓ test_epub_full_generation passed")

    print("\n✅ All EPUB tests passed!")
