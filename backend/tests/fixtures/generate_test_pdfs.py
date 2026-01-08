"""
Generate synthetic test PDFs for load testing.

This script creates sample PDFs that can be used for load testing when
real test PDFs are not available.
"""

import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_JUSTIFY
except ImportError:
    print("Error: reportlab not installed. Install with: pip install reportlab")
    exit(1)


def create_simple_text_pdf(output_path: Path, num_pages: int = 15):
    """
    Create a simple text-only PDF (10-20 pages).

    Args:
        output_path: Path to save the PDF
        num_pages: Number of pages to generate (default: 15)
    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    for i in range(num_pages):
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, f"Chapter {i + 1}: Load Testing Document")

        # Body text
        c.setFont("Helvetica", 12)
        y = height - 120

        paragraphs = [
            "This is a simple text document generated for load testing purposes.",
            "It contains multiple pages of text to simulate a typical PDF conversion scenario.",
            "",
            "Load testing helps us validate that the system can handle expected load",
            "and meets performance targets. This document is specifically designed to test",
            "the baseline performance of simple PDF conversions.",
            "",
            "Performance targets:",
            "- Upload to processing to download: < 30 seconds end-to-end",
            "- EPUB file size: ≤ 120% of original PDF size",
            "",
            f"This is page {i + 1} of {num_pages}.",
        ]

        for para in paragraphs:
            c.drawString(72, y, para)
            y -= 20

        # Page number at bottom
        c.setFont("Helvetica", 10)
        c.drawString(width / 2, 36, f"Page {i + 1}")

        c.showPage()

    c.save()
    print(f"Created: {output_path} ({num_pages} pages)")


def create_complex_technical_pdf(output_path: Path, num_pages: int = 300):
    """
    Create a complex technical PDF with multiple pages.

    Note: This is a simplified version. In production, you would use
    real technical documents with tables, images, and equations.

    Args:
        output_path: Path to save the PDF
        num_pages: Number of pages to generate (default: 300)
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    styles['Normal'].alignment = TA_JUSTIFY

    # Title page
    story.append(Paragraph("<b>Technical Manual: Load Testing System</b>", styles['Title']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Version 1.0", styles['Normal']))
    story.append(PageBreak())

    # Generate chapters
    chapters = num_pages // 10  # ~10 pages per chapter

    for chapter in range(chapters):
        # Chapter title
        story.append(Paragraph(f"<b>Chapter {chapter + 1}: System Architecture</b>", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))

        # Chapter content
        content = [
            f"This chapter discusses the architecture of the load testing system for PDF to EPUB conversion. "
            f"The system consists of multiple components including a web frontend, API backend, worker processes, "
            f"and database storage.",
            "",
            "<b>Key Components:</b>",
            "1. Frontend: Next.js application for user interface",
            "2. Backend API: FastAPI service for handling requests",
            "3. Worker: Celery workers for async processing",
            "4. Database: Supabase PostgreSQL for data storage",
            "5. Cache: Redis for job queue and caching",
            "",
            "The system is designed to handle concurrent conversions with performance targets of 300-page documents "
            "in under 2 minutes and simple documents in under 30 seconds.",
        ]

        for para in content:
            if para:
                story.append(Paragraph(para, styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))

        # Add subsections
        for section in range(3):
            story.append(Paragraph(f"<b>Section {chapter + 1}.{section + 1}: Technical Details</b>",
                                   styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))

            subsection_content = [
                "This section provides detailed technical information about the system implementation. "
                "Performance testing validates that the system meets all non-functional requirements.",
                "",
                "Load testing scenarios include baseline performance, concurrent load, and stress testing "
                "with up to 50 simultaneous users.",
            ]

            for para in subsection_content:
                if para:
                    story.append(Paragraph(para, styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))

        story.append(PageBreak())

    doc.build(story)
    print(f"Created: {output_path} (~{num_pages} pages)")


def create_placeholder_pdf(output_path: Path, filename: str):
    """
    Create a placeholder PDF with instructions.

    Args:
        output_path: Path to save the PDF
        filename: Name of the PDF file
    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, f"Placeholder: {filename}")

    c.setFont("Helvetica", 12)
    c.drawString(72, height - 120, "This is a placeholder PDF file.")
    c.drawString(72, height - 140, "Replace with actual test PDF for comprehensive load testing.")

    c.save()
    print(f"Created placeholder: {output_path}")


def main():
    """Generate all test PDFs."""
    # Determine output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "load-test-pdfs"
    output_dir.mkdir(exist_ok=True)

    print("Generating test PDFs for load testing...")
    print(f"Output directory: {output_dir}")
    print()

    # Create simple text PDF (10-20 pages)
    create_simple_text_pdf(output_dir / "simple-text.pdf", num_pages=15)

    # Create complex technical PDF (300 pages)
    create_complex_technical_pdf(output_dir / "complex-technical.pdf", num_pages=300)

    # Create placeholders for optional test files
    create_placeholder_pdf(output_dir / "multi-language.pdf", "multi-language.pdf")
    create_placeholder_pdf(output_dir / "large-file.pdf", "large-file.pdf")
    create_placeholder_pdf(output_dir / "edge-case.pdf", "edge-case.pdf")

    print()
    print("✓ Test PDFs generated successfully!")
    print()
    print("Next steps:")
    print("1. Review the generated PDFs in:", output_dir)
    print("2. Replace placeholders with real PDFs if available")
    print("3. Run load tests: locust -f tests/load/scenarios.py --host http://localhost:8000")


if __name__ == "__main__":
    main()
