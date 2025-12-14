# AI Integration Guide

**Project:** Transfer2Read - AI Layout Analysis
**Date:** 2025-12-13
**Story:** 4.2 - LangChain AI Layout Analysis Integration

---

## Overview

This guide explains how to integrate and configure the AI-powered PDF layout analysis system. Transfer2Read uses **GPT-4o** (primary) and **Claude 3.5 Haiku** (fallback) via **LangChain** to detect complex document elements like tables, equations, images, and multi-column layouts.

### Key Features

- **Dual AI Provider System:** GPT-4o for high-quality analysis with automatic fallback to Claude
- **Structured Output:** Pydantic models ensure consistent JSON schema
- **Retry Logic:** Exponential backoff for transient failures (1min, 5min, 15min)
- **Concurrent Processing:** Analyze 4 pages in parallel using asyncio
- **Progress Reporting:** Real-time job status updates via Celery

---

## Architecture

### Components

```
backend/app/
├── services/
│   ├── ai/                          # AI Providers
│   │   ├── base.py                  # Abstract base class
│   │   ├── gpt4.py                  # GPT-4o implementation
│   │   ├── claude.py                # Claude 3.5 Haiku implementation
│   │   └── layout_analyzer.py       # Orchestration with retry/fallback
│   └── conversion/
│       ├── document_loader.py       # PyMuPDF PDF extraction
│       └── batch_analyzer.py        # Concurrent page processing
├── schemas/
│   └── layout_analysis.py           # Pydantic models (LayoutDetection, etc.)
└── tasks/
    └── conversion_pipeline.py       # Celery task integration
```

### Data Flow

1. **PDF Upload** → Stored in Supabase Storage
2. **Celery Task Triggered** → `analyze_layout(job_id)`
3. **PDF Download** → Temp file from Supabase
4. **Page Extraction** → PyMuPDF converts pages to images + text
5. **Concurrent Analysis** → BatchAnalyzer processes 4 pages at a time
6. **AI Analysis** → GPT-4o or Claude (fallback) detects elements
7. **Results Stored** → Database + job status update
8. **Temp Cleanup** → Delete local PDF file

---

## Setup Instructions

### 1. API Keys

#### OpenAI API Key (Required)

1. Create account at [platform.openai.com](https://platform.openai.com)
2. Navigate to **API Keys** section
3. Click **Create new secret key**
4. Copy key (starts with `sk-...`)
5. Add to `.env`:

```bash
OPENAI_API_KEY=sk-proj-...your-key-here...
```

**Cost:** ~$0.005-0.02 per page (GPT-4o with vision)

#### Anthropic API Key (Required for Fallback)

1. Create account at [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **API Keys**
3. Click **Create Key**
4. Copy key (starts with `sk-ant-...`)
5. Add to `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

**Cost:** ~$0.002-0.01 per page (Claude 3.5 Haiku)

### 2. Environment Variables

Add to `backend/.env`:

```bash
# AI API Keys
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY
ANTHROPIC_API_KEY=sk-ant-YOUR_ANTHROPIC_KEY

# AI Analysis Configuration
ANALYSIS_CONCURRENCY=4              # Pages analyzed concurrently
ANALYSIS_PAGE_BATCH_SIZE=5          # Progress update frequency
ANALYSIS_TIMEOUT_PER_PAGE=30        # Timeout per page (seconds)
MAX_IMAGE_SIZE=2048                 # Max pixel dimension for vision input
AI_ANALYSIS_MAX_RETRIES=3           # Max retries before fallback
AI_FALLBACK_ENABLED=true            # Enable Claude fallback
```

### 3. Verify Configuration

Test API connectivity:

```bash
cd backend
source venv/bin/activate
python -c "from app.services.ai.gpt4 import GPT4Provider; print(GPT4Provider('$OPENAI_API_KEY').initialize_client())"
```

Expected output: `ChatOpenAI(model='gpt-4o', ...)`

### 4. Database Migration

Apply migration to add AI columns:

```bash
# Connect to Supabase dashboard
# Navigate to SQL Editor
# Run: backend/supabase/migrations/005_ai_layout_analysis_columns.sql
```

Or use Supabase CLI:

```bash
supabase db push
```

---

## Model Selection Strategy

### When GPT-4o is Used

- **Default:** All page analysis starts with GPT-4o
- **Quality:** Best for complex layouts, equations, multi-column documents
- **Speed:** 2-5 seconds per page (API latency included)
- **Cost:** Higher but more accurate

### When Claude 3.5 Haiku is Used

- **Fallback:** Automatically triggered on GPT-4o failures:
  - Timeout errors
  - Rate limiting
  - Network issues
  - After 3 retries exhausted
- **Quality:** Good for simpler text-heavy documents
- **Speed:** 1-3 seconds per page
- **Cost:** ~5x cheaper than GPT-4o

### Mixed Mode

If some pages fail with GPT-4o and fallback to Claude, `ai_model_used` is set to `"mixed"` in the database.

---

## Fallback Behavior

### Automatic Fallback

1. **Transient Error Detected:** Timeout, rate limit, network error
2. **Retry with Exponential Backoff:**
   - Attempt 1: Wait 1 minute, retry GPT-4o
   - Attempt 2: Wait 5 minutes, retry GPT-4o
   - Attempt 3: Wait 15 minutes, retry GPT-4o
3. **All Retries Exhausted:** Switch to Claude 3.5 Haiku
4. **Claude Success:** Continue with Claude for remaining pages
5. **Claude Failure:** Raise exception, mark job as FAILED

### Permanent Errors (No Retry)

These errors fail immediately without retries:

- Invalid API key
- Model not found
- Authentication failed
- Unauthorized access

### Disabling Fallback

To disable Claude fallback (GPT-4o only mode):

```bash
AI_FALLBACK_ENABLED=false
```

**Warning:** Jobs will fail if GPT-4o is unavailable.

---

## Token Cost Estimation

### GPT-4o Pricing

- **Input:** $2.50 per 1M tokens
- **Output:** $10 per 1M tokens
- **Vision:** ~170 tokens per image (1920x1440)

**Per Page Estimate:**

- Text (1 page): ~500-1000 input tokens
- Image: ~170 tokens
- Response: ~200-500 output tokens
- **Total Cost:** $0.005 - $0.02 per page

### Claude 3.5 Haiku Pricing

- **Input:** $0.80 per 1M tokens (~3x cheaper than GPT-4o)
- **Output:** $4 per 1M tokens (~2.5x cheaper)

**Per Page Estimate:** $0.002 - $0.01 per page

### 100-Page Document Cost

- **GPT-4o Only:** $0.50 - $2.00
- **Claude Only:** $0.20 - $1.00
- **Mixed (80% GPT-4o, 20% Claude):** $0.45 - $1.80

---

## Monitoring and Logging

### Log Locations

- **Application Logs:** `backend/logs/app.log`
- **AI Analysis Logs:** Filter by `layout_analyzer` or `batch_analyzer`

### Key Log Events

```log
INFO - GPT-4o client initialized successfully (timeout: 30s)
INFO - Job abc-123: Loaded 25 pages, starting concurrent analysis...
INFO - Page 3 analyzed successfully: 2 tables, 1 images, 0 equations (confidence: 95%)
WARNING - GPT-4o timeout on page 5 (attempt 1/3), retrying in 60s...
INFO - Page 5 analyzed successfully with Claude fallback
INFO - Job abc-123: Batch analysis complete. Success: 25/25 pages
```

### Monitoring Token Usage

Track API usage in respective dashboards:

- **OpenAI:** [platform.openai.com/usage](https://platform.openai.com/usage)
- **Anthropic:** [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing)

### Database Tracking

Query token usage from `conversion_jobs` table:

```sql
SELECT
  id,
  ai_model_used,
  token_usage,
  (layout_analysis->'total_pages')::int AS pages
FROM conversion_jobs
WHERE ai_model_used IS NOT NULL
ORDER BY created_at DESC;
```

---

## Troubleshooting

### "Invalid API key" Error

**Symptoms:** Immediate failure, no retries

**Solutions:**

1. Verify API key is correct (starts with `sk-` for OpenAI, `sk-ant-` for Anthropic)
2. Check key hasn't expired or been revoked
3. Ensure environment variable is loaded: `echo $OPENAI_API_KEY`
4. Restart backend service after updating `.env`

### "Rate limit exceeded" Error

**Symptoms:** 429 errors, automatic retries triggered

**Solutions:**

1. **Wait for Retry:** System automatically retries with backoff
2. **Reduce Concurrency:** Lower `ANALYSIS_CONCURRENCY` (e.g., 2 instead of 4)
3. **Upgrade API Plan:** Increase rate limits at provider dashboard
4. **Enable Fallback:** Ensure `AI_FALLBACK_ENABLED=true` for Claude fallback

### Analysis Taking Too Long

**Symptoms:** Job stuck at "ANALYZING" for >10 minutes

**Solutions:**

1. **Check Logs:** Look for timeout errors or retries
2. **Increase Timeout:** Adjust `ANALYSIS_TIMEOUT_PER_PAGE` (e.g., 60 seconds)
3. **Reduce Concurrency:** Lower to 2-3 concurrent pages
4. **Check Network:** Verify backend can reach OpenAI/Anthropic APIs

### All Pages Failing

**Symptoms:** "failure rate >20%" exception

**Solutions:**

1. **API Outage:** Check status pages:
   - OpenAI: [status.openai.com](https://status.openai.com)
   - Anthropic: [status.anthropic.com](https://status.anthropic.com)
2. **Network Issues:** Verify outbound HTTPS connections allowed
3. **API Credits:** Ensure billing account has available credits
4. **Model Availability:** Confirm `gpt-4o` and `claude-3-5-haiku-20241022` models accessible

### Fallback Not Working

**Symptoms:** GPT-4o fails but Claude never tries

**Solutions:**

1. Verify `AI_FALLBACK_ENABLED=true`
2. Check `ANTHROPIC_API_KEY` is set and valid
3. Review logs for "fallback" keyword
4. Ensure `ClaudeProvider` initialization successful

---

## Performance Optimization

### Concurrent Processing

Default: 4 pages analyzed simultaneously

**Adjust for Performance:**

```bash
# Faster (more API calls, higher rate limit risk)
ANALYSIS_CONCURRENCY=8

# Slower (safer, lower rate limit risk)
ANALYSIS_CONCURRENCY=2
```

### Image Size Optimization

Reduce vision token usage by resizing large pages:

```bash
# Default: 2048px max dimension
MAX_IMAGE_SIZE=2048

# Lower quality, faster, cheaper
MAX_IMAGE_SIZE=1024

# Higher quality, slower, more expensive
MAX_IMAGE_SIZE=4096
```

### Batch Size for Progress Updates

Control how often job status updates:

```bash
# Update every 5 pages (default)
ANALYSIS_PAGE_BATCH_SIZE=5

# More frequent updates (more DB writes)
ANALYSIS_PAGE_BATCH_SIZE=2

# Less frequent (fewer DB writes, less user feedback)
ANALYSIS_PAGE_BATCH_SIZE=10
```

---

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/unit/services/ai/test_layout_analyzer.py -v
```

### Run Integration Tests

```bash
pytest tests/integration/test_layout_analysis.py -v
```

### Performance Test (Mocked AI)

Test 100-page analysis (mocked responses, fast):

```bash
pytest tests/integration/test_layout_analysis.py::test_performance_100_pages -v
```

**Expected:** <10 minutes with mocked AI

---

## Example Usage

### Programmatic API

```python
from backend.app.services.conversion.batch_analyzer import create_batch_analyzer
import asyncio

# Create analyzer
analyzer = create_batch_analyzer()

# Define progress callback
def on_progress(completed, total):
    print(f"Progress: {completed}/{total} pages analyzed")

# Run analysis
async def analyze():
    results = await analyzer.analyze_all_pages(
        job_id="test-job-123",
        pdf_path="/path/to/document.pdf",
        progress_callback=on_progress
    )

    # Access results
    for page in results:
        print(f"Page {page.page_number}: {page.tables.count} tables, {page.images.count} images")

# Execute
asyncio.run(analyze())
```

### Celery Task

```python
from backend.app.tasks.conversion_pipeline import analyze_layout

# Dispatch analysis task
result = analyze_layout.delay("job-uuid-here")

# Check status
print(result.status)  # PENDING, SUCCESS, FAILURE
```

---

## References

- **LangChain Documentation:** [python.langchain.com](https://python.langchain.com/)
- **OpenAI GPT-4o Vision:** [platform.openai.com/docs/guides/vision](https://platform.openai.com/docs/guides/vision)
- **Anthropic Claude API:** [docs.anthropic.com](https://docs.anthropic.com/)
- **PyMuPDF Documentation:** [pymupdf.readthedocs.io](https://pymupdf.readthedocs.io/)

---

**Last Updated:** 2025-12-13
**Maintained by:** xavier
**Questions:** See project documentation or GitHub issues

---

## EPUB Generation

**Story:** 4.4 - EPUB Generation from AI-Analyzed Content

### Overview

The EPUB Generation service converts AI-analyzed PDF content into valid EPUB 3.0 files with preserved formatting. It uses the `ebooklib` library to create reflowable e-books that work across all major e-readers.

### Key Features

- **EPUB 3.0 Compliance:** Valid EPUB structure with NCX (EPUB 2) and Nav (EPUB 3) support
- **AI Content Assembly:** Converts detected tables, images, and equations to XHTML
- **Metadata Extraction:** Automatic title, author, and cover generation from PDF
- **Responsive CSS:** E-reader compatible stylesheet with dark mode support
- **Multi-Language Support:** Font embedding for CJK characters (CN, JP, KR, VI)
- **Validation:** Structure checks and file size constraints (≤ 120% of PDF)

### Architecture

```
backend/app/services/conversion/
├── epub_generator.py           # Main EPUB orchestrator
├── content_assembler.py        # AI data → XHTML conversion
├── metadata_extractor.py       # PDF metadata extraction
├── epub_validator.py           # EPUB validation
├── toc_generator.py            # NCX and Nav generation (reused from Story 4.3)
└── templates/
    └── epub_styles.css         # Master CSS stylesheet
```

### EPUB Generation Pipeline

1. **Initialize EPUB Book** → Create `epub.EpubBook()` with unique ID
2. **Extract Metadata** → Parse PDF metadata (title, author, language)
3. **Generate Cover** → Render first page as thumbnail (800x1200px)
4. **Assemble Chapters** → Convert document structure + layout analysis to XHTML
5. **Embed Content:**
   - Tables → HTML `<table>` with responsive CSS
   - Images → Embedded with `<img>` tags and captions
   - Equations → MathML with PNG fallback
6. **Generate TOC** → Build NCX (EPUB 2) and Nav (EPUB 3) navigation
7. **Add Stylesheet** → Embed responsive CSS with dark mode support
8. **Validate Structure** → Check file references and XHTML well-formedness
9. **Upload to Storage** → Supabase Storage at `downloads/{user_id}/{job_id}/output.epub`
10. **Generate Download URL** → Signed URL with 1-hour expiration

### Configuration

Add to `backend/.env`:

```bash
# EPUB Generation Configuration
EPUB_MAX_FILE_SIZE_MB=100         # Max EPUB size before compression
EPUB_IMAGE_QUALITY=85             # JPEG quality for image compression (0-100)
EPUB_VALIDATION_ENABLED=true      # Enable epubcheck validation
EPUB_GENERATION_TIMEOUT=600       # 10 minutes max for EPUB generation
EPUB_COVER_WIDTH=800              # Cover image width in pixels
EPUB_COVER_HEIGHT=1200            # Cover image height in pixels
```

### Dependencies

Required Python packages (in `requirements.txt`):

```txt
ebooklib                # EPUB 3.0 creation
pymupdf==1.24.10       # PDF metadata extraction and rendering
Pillow                 # Image processing and compression
lxml                   # XML validation for EPUB XHTML
```

Install:

```bash
pip install -r backend/requirements.txt
```

### Content Assembly Examples

#### Table Conversion

AI-detected table → HTML table:

```python
# Input: layout_analysis["tables"][0]
table_data = {
    "bbox": [100, 200, 500, 400],
    "rows": [
        ["Header 1", "Header 2", "Header 3"],
        ["Data 1", "Data 2", "Data 3"]
    ],
    "confidence": 95
}

# Output: HTML table with CSS
html = """
<table class="ai-table">
    <thead>
        <tr><th>Header 1</th><th>Header 2</th><th>Header 3</th></tr>
    </thead>
    <tbody>
        <tr><td>Data 1</td><td>Data 2</td><td>Data 3</td></tr>
    </tbody>
</table>
"""
```

#### Image Embedding

```python
# Input: layout_analysis["images"][0]
image_data = {
    "bbox": [50, 100, 300, 250],
    "page": 5,
    "image_bytes": b"...",  # PNG or JPEG data
    "description": "Figure 1: System Architecture"
}

# Output: Figure with caption
html = """
<figure>
    <img src="../images/page-5-img-1.png" alt="Figure 1"/>
    <figcaption>Figure 1: System Architecture</figcaption>
</figure>
"""
```

#### Equation Handling

```python
# Input: layout_analysis["equations"][0]
equation_data = {
    "latex": "E = mc^2",
    "mathml": "<math><mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></msup></math>",
    "png_fallback": b"...",  # Rendered PNG
    "confidence": 97
}

# Output: MathML with PNG fallback
html = """
<math xmlns="http://www.w3.org/1998/Math/MathML">
    <mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></msup>
</math>
<img src="../images/equation-1.png" alt="E = mc^2" class="math-fallback"/>
"""
```

### Responsive CSS Stylesheet

The EPUB stylesheet (`epub_styles.css`) includes:

- **Typography:** Georgia/Times serif with 1.6 line height, justified text
- **Tables:** Responsive horizontal scroll on small screens
- **Images:** Max-width 100% with auto height, centered
- **Equations:** Center-aligned with math symbol fonts
- **Headings:** H1-H4 hierarchy with page breaks
- **Dark Mode:** `@media (prefers-color-scheme: dark)` support
- **Accessibility:** High contrast mode support

### File Size Validation

EPUB files must be ≤ 120% of original PDF size (FR37):

```python
from app.services.conversion.epub_validator import EpubValidator

validator = EpubValidator()
is_ok, message = validator.check_file_size(
    epub_size_bytes=12_000_000,  # 12 MB
    pdf_size_bytes=10_000_000,   # 10 MB
    max_ratio=1.2  # 120%
)

if not is_ok:
    # Compress images or warn user
    print(message)  # "EPUB oversized: 120% of PDF size (max: 120%)"
```

### EPUB Structure

Standard EPUB 3.0 structure:

```
output.epub (ZIP archive)
├── mimetype                      # "application/epub+zip"
├── META-INF/
│   └── container.xml             # Points to content.opf
├── OEBPS/                        # Main content directory
│   ├── content.opf               # Package document (metadata, manifest, spine)
│   ├── toc.ncx                   # Navigation (EPUB 2 compatibility)
│   ├── nav.xhtml                 # Navigation (EPUB 3)
│   ├── styles.css                # Master stylesheet
│   ├── images/                   # Embedded images
│   │   ├── cover.png
│   │   ├── page-5-img-1.png
│   │   └── equation-1.png
│   └── chapters/                 # XHTML chapter files
│       ├── chapter-1.xhtml
│       ├── chapter-2.xhtml
│       └── chapter-3.xhtml
```

### Programmatic Usage

```python
from app.services.conversion.epub_generator import EpubGenerator
from app.schemas.document_structure import DocumentStructure
from app.schemas.layout_analysis import PageAnalysis

# Create generator
generator = EpubGenerator(job_id="abc123", user_id="user_xyz")

# Prepare data
document_structure = DocumentStructure(**structure_dict)
layout_analysis = [PageAnalysis(**page_dict) for page_dict in layout_list]

# Generate EPUB
epub_bytes, epub_metadata = generator.generate(
    document_structure=document_structure,
    layout_analysis=layout_analysis,
    pdf_bytes=original_pdf_bytes
)

# Upload to storage
from app.services.storage.supabase_storage import SupabaseStorageService

storage = SupabaseStorageService()
storage.upload_file(
    bucket="downloads",
    path=f"downloads/{user_id}/{job_id}/output.epub",
    file_data=epub_bytes,
    content_type="application/epub+zip"
)
```

### Celery Task Integration

EPUB generation is automatically triggered in the conversion pipeline:

```python
# Pipeline flow (Story 4.1)
workflow = chain(
    analyze_layout.s(job_id),        # Story 4.2
    extract_content.s(),             # Story 4.2
    identify_structure.s(),          # Story 4.3
    generate_epub.s(),               # Story 4.4 ← THIS TASK
    calculate_quality_score.s()      # Story 4.5
)
```

Progress updates:
- **85%:** "Generating EPUB file..."
- **95%:** "Uploading EPUB to storage..."
- **100%:** "COMPLETED" with `download_url` in metadata

### Testing

#### Unit Tests

```bash
pytest tests/unit/services/conversion/test_epub_generator.py -v
pytest tests/unit/services/conversion/test_content_assembler.py -v
pytest tests/unit/services/conversion/test_epub_validator.py -v
```

#### Integration Test

```bash
pytest tests/integration/test_epub_generation.py -v
```

Test full pipeline with sample PDF:

```python
def test_full_epub_generation():
    # Load sample PDF (50 pages, tables, images)
    with open("tests/fixtures/sample.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Mock AI analysis results
    document_structure = load_fixture("document_structure.json")
    layout_analysis = load_fixture("layout_analysis.json")

    # Generate EPUB
    generator = EpubGenerator(job_id="test", user_id="test_user")
    epub_bytes, metadata = generator.generate(
        document_structure=document_structure,
        layout_analysis=layout_analysis,
        pdf_bytes=pdf_bytes
    )

    # Validate EPUB
    validator = EpubValidator()
    is_valid, errors, warnings = validator.validate_epub_structure(epub_bytes)
    assert is_valid, f"EPUB validation failed: {errors}"

    # Check metadata
    assert metadata["title"] is not None
    assert metadata["size_bytes"] > 0
```

### Compatibility Testing

Open generated EPUB in multiple readers:

1. **Apple Books (macOS/iOS):**
   - Verify TOC navigation works
   - Check image rendering quality
   - Test dark mode support

2. **Calibre Viewer:**
   - Verify table layouts (responsive scroll)
   - Check equation rendering (MathML or PNG)
   - Test multi-language character display

3. **Kindle Previewer:**
   - Verify EPUB 3 → KF8 conversion
   - Check reflowable layout
   - Test font rendering

### Troubleshooting

#### "Invalid EPUB structure" Error

**Solutions:**
1. Check `epub_validator.py` errors list for details
2. Verify all referenced images/chapters exist
3. Validate XHTML well-formedness with `lxml`

#### EPUB Oversized (>120% of PDF)

**Solutions:**
1. Enable image compression: `EPUB_IMAGE_QUALITY=75`
2. Reduce cover image size: `EPUB_COVER_WIDTH=600`
3. Check for duplicate embedded images

#### Missing Fonts for CJK Characters

**Solutions:**
1. Verify font files in `templates/fonts/` directory
2. Check CSS `@font-face` rules are embedded
3. Test with sample Chinese/Japanese text

#### Cover Image Not Rendering

**Solutions:**
1. Check PDF has at least 1 page
2. Verify PyMuPDF `get_pixmap()` successful
3. Check cover image dimensions (800x1200)

### Performance

- **Small PDFs (<10 pages):** <5 seconds
- **Medium PDFs (50 pages):** 10-20 seconds
- **Large PDFs (500 pages):** 2-5 minutes

Bottlenecks:
- Cover generation: ~1-2 seconds (PyMuPDF rendering)
- XHTML assembly: ~0.5 seconds per chapter
- EPUB compression: ~1-5 seconds (ZIP creation)
- Upload to storage: ~2-10 seconds (network-dependent)

---

## Quality Assurance and Confidence Scoring

**Story:** 4.5 - AI-Based Quality Assurance & Confidence Scoring

### Overview

The Quality Assurance system calculates confidence scores from AI analysis results to provide users with transparency about conversion fidelity. It aggregates confidence metrics from layout and structure analysis, generates warnings for low-confidence elements, and validates against PRD quality targets.

### Key Features

- **Confidence Score Calculation:** Weighted average across all detected elements (text, tables, images, equations)
- **Element Count Tracking:** Comprehensive count of detected elements for transparency
- **Warning Generation:** Automatic flags for low-confidence elements (<80%)
- **Fidelity Target Validation:** Validates against PRD targets (95%+ complex, 99%+ text)
- **Progressive Calculation:** Quality scores calculated at each pipeline stage
- **Graceful Degradation:** Continues pipeline even if quality scoring fails

### Architecture

```
backend/app/
├── services/
│   └── conversion/
│       └── quality_scorer.py         # Core quality calculation logic
├── schemas/
│   └── quality_report.py             # QualityReport Pydantic models
├── tasks/
│   └── conversion_pipeline.py        # Integration with calculate_quality_score task
└── api/v1/
    └── jobs.py                       # quality_report in API responses
```

### Quality Scoring Pipeline

1. **Layout Analysis (Story 4.2)** → Extract AI confidence scores per element
2. **Structure Analysis (Story 4.3)** → Extract TOC detection confidence
3. **EPUB Generation (Story 4.4)** → Finalize content assembly
4. **Quality Calculation (Story 4.5)** → Generate complete quality report:
   - Calculate overall confidence (weighted average)
   - Count detected elements (tables, images, equations, chapters)
   - Generate warnings for low-confidence items
   - Validate against fidelity targets
5. **Database Storage** → Store `quality_report` JSONB in `conversion_jobs`
6. **API Response** → Include quality report in job details

### Configuration

Add to `backend/.env`:

```bash
# Quality Scoring Configuration
QUALITY_SCORING_ENABLED=true         # Enable quality calculation
QUALITY_WARNING_THRESHOLD=80         # Flag confidence below this threshold
QUALITY_TARGET_COMPLEX=95            # FR24: Complex PDF fidelity target
QUALITY_TARGET_TEXT=99               # FR25: Text-based PDF fidelity target
QUALITY_TEXT_BASE_CONFIDENCE=99      # Base confidence for simple text blocks
```

### Confidence Calculation Algorithm

#### Weighted Average Formula

```python
def calculate_overall_confidence(elements: dict) -> float:
    """
    Calculate weighted average confidence across all detected elements.

    Weights:
    - Text blocks: 99% base (assumed high quality OCR)
    - Tables: AI confidence (varies 50-100%)
    - Images: 100% (copied as-is, no transformation)
    - Equations: AI confidence (varies 60-100% depending on notation complexity)
    - Multi-column: AI confidence on reflow strategy (70-95%)

    Formula: weighted_sum(confidence * element_count) / total_elements
    """
    total_score = 0
    total_weight = 0

    # Text blocks (assume 99% baseline)
    text_blocks = elements.get("text_blocks", [])
    total_score += len(text_blocks) * 99
    total_weight += len(text_blocks)

    # Tables (use AI confidence)
    for table in elements.get("tables", []):
        total_score += table["confidence"] * 100
        total_weight += 1

    # Images (100% - no analysis needed)
    images = elements.get("images", [])
    total_score += len(images) * 100
    total_weight += len(images)

    # Equations (use AI confidence)
    for equation in elements.get("equations", []):
        total_score += equation["confidence"] * 100
        total_weight += 1

    # Calculate average
    if total_weight == 0:
        return 99.0  # Default for empty documents

    return round(total_score / total_weight, 2)
```

#### Example Calculations

**Simple Text Document:**
- 100 text blocks × 99% = 99% overall confidence
- Classification: Text-based document → 99%+ target
- **Result:** ✅ Target met

**Complex Document:**
- 50 text blocks × 99% = 4950
- 10 tables × 85% avg = 850
- 5 images × 100% = 500
- 3 equations × 90% avg = 270
- Total: 6570 / 68 elements = **96.6% overall confidence**
- Classification: Complex document → 95%+ target
- **Result:** ✅ Target met

**Low-Confidence Document:**
- 20 text blocks × 99% = 1980
- 5 tables × 65% avg = 325 (⚠️ low confidence)
- 2 equations × 55% avg = 110 (⚠️ low confidence)
- Total: 2415 / 27 = **89.4% overall confidence**
- Classification: Complex document → 95%+ target
- **Result:** ❌ Target NOT met
- **Warnings:** 2 tables + 2 equations flagged

### Quality Report JSON Schema

#### QualityReport Structure

```json
{
  "overall_confidence": 95.2,
  "elements": {
    "tables": {
      "count": 12,
      "avg_confidence": 93.5,
      "low_confidence_items": [
        {"page": 45, "confidence": 72}
      ]
    },
    "images": {
      "count": 8,
      "avg_confidence": 100.0,
      "low_confidence_items": []
    },
    "equations": {
      "count": 5,
      "avg_confidence": 97.0,
      "low_confidence_items": []
    },
    "chapters": {
      "count": 15,
      "detected_toc": true
    },
    "multi_column_pages": {
      "count": 3,
      "pages": [5, 12, 18]
    }
  },
  "warnings": [
    "[WARNING] Page 45: Table detected but low confidence (72%) - complex structure may not be fully preserved. Manual review recommended."
  ],
  "fidelity_targets": {
    "complex_elements": {
      "target": 95,
      "actual": 93.5,
      "met": false
    }
  }
}
```

#### Pydantic Model Definition

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any

class QualityReport(BaseModel):
    """Complete quality assurance report for conversion job."""

    overall_confidence: Optional[float] = Field(
        None, ge=0, le=100,
        description="Overall document confidence score (null if unavailable)"
    )
    elements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Quality metrics per element type"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="User-facing warnings for low confidence elements"
    )
    fidelity_targets: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fidelity target validation results"
    )

    @field_validator('overall_confidence')
    @classmethod
    def validate_overall_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Ensure overall confidence is within 0-100 range"""
        if v is not None and not (0 <= v <= 100):
            raise ValueError(f"overall_confidence must be 0-100, got {v}")
        return v
```

### Warning Generation

#### Warning Thresholds

- **Below 80%:** WARNING generated with manual review recommendation
- **Below 60%:** CRITICAL warning - strong recommendation for review

#### Warning Message Examples

```
[WARNING] Page 45: Table detected but low confidence (72%) - complex structure may not be fully preserved. Manual review recommended.

[CRITICAL] Equation on page 23: Low confidence (55%) - unusual notation detected. Verify accuracy in final EPUB.

[WARNING] Page 12: Multi-column layout with low confidence (75%) - reading order may need verification.
```

#### Warning Logic

```python
def generate_warnings(layout_analysis: Dict, threshold: float = 80.0) -> List[str]:
    """Generate user-facing warnings for low-confidence elements."""
    warnings = []
    pages = layout_analysis.get("pages", [])

    for page in pages:
        page_num = page.get("page_number", 0)

        # Check tables
        tables = page.get("tables", {}).get("items", [])
        for table in tables:
            confidence = table.get("confidence", 0)
            if confidence < threshold:
                severity = "CRITICAL" if confidence < 60 else "WARNING"
                warnings.append(
                    f"[{severity}] Page {page_num}: Table detected but low "
                    f"confidence ({confidence:.0f}%) - complex structure may "
                    f"not be fully preserved. Manual review recommended."
                )

        # Check equations
        equations = page.get("equations", {}).get("items", [])
        for equation in equations:
            confidence = equation.get("confidence", 0)
            if confidence < threshold:
                severity = "CRITICAL" if confidence < 60 else "WARNING"
                warnings.append(
                    f"[{severity}] Equation on page {page_num}: Low confidence "
                    f"({confidence:.0f}%) - unusual notation detected. "
                    f"Verify accuracy in final EPUB."
                )

    return warnings
```

### Fidelity Target Validation

#### PRD Requirements (FR24, FR25)

- **Complex PDFs:** 95%+ fidelity target (documents with tables, equations, diagrams)
- **Text-Based PDFs:** 99%+ fidelity target (documents with only text)

#### Validation Logic

```python
def validate_fidelity_targets(
    overall_confidence: float,
    layout_analysis: Dict
) -> Dict[str, Any]:
    """Validate actual confidence against PRD fidelity targets."""
    fidelity_targets = {}

    # Determine document complexity
    pages = layout_analysis.get("pages", [])
    has_complex_elements = False

    for page in pages:
        tables_count = page.get("tables", {}).get("count", 0)
        equations_count = page.get("equations", {}).get("count", 0)
        if tables_count > 0 or equations_count > 0:
            has_complex_elements = True
            break

    if has_complex_elements:
        # Complex document: target 95%+
        fidelity_targets["complex_elements"] = {
            "target": 95,
            "actual": overall_confidence,
            "met": overall_confidence >= 95
        }
    else:
        # Text-based document: target 99%+
        fidelity_targets["text_based"] = {
            "target": 99,
            "actual": overall_confidence,
            "met": overall_confidence >= 99
        }

    return fidelity_targets
```

### API Integration

#### GET /api/v1/jobs/{job_id}

Quality report included in job details response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "COMPLETED",
  "input_path": "uploads/user-id/job-id/input.pdf",
  "output_path": "downloads/user-id/job-id/output.epub",
  "progress": 100,
  "stage_metadata": {
    "current_stage": "COMPLETED",
    "progress_percent": 100,
    "quality_confidence": 95.2,
    "completed_at": "2025-12-13T10:32:15Z"
  },
  "quality_report": {
    "overall_confidence": 95.2,
    "elements": {
      "tables": {"count": 12, "avg_confidence": 93.5},
      "images": {"count": 8, "avg_confidence": 100.0},
      "equations": {"count": 5, "avg_confidence": 97.0}
    },
    "warnings": [],
    "fidelity_targets": {
      "complex_elements": {"target": 95, "actual": 95.2, "met": true}
    }
  },
  "created_at": "2025-12-13T10:30:00Z",
  "completed_at": "2025-12-13T10:32:15Z"
}
```

### Database Storage

#### Migration Script

```sql
-- backend/supabase/migrations/007_quality_report_column.sql

-- Add quality_report column to conversion_jobs table
ALTER TABLE conversion_jobs
ADD COLUMN IF NOT EXISTS quality_report JSONB DEFAULT '{}'::jsonb;

-- Add GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_conversion_jobs_quality_report
ON conversion_jobs USING GIN (quality_report);

-- Add comment for documentation
COMMENT ON COLUMN conversion_jobs.quality_report IS
'Quality assurance metrics including confidence scores, element counts, warnings, and fidelity validation';
```

#### Query Examples

**Find jobs with low overall confidence:**

```sql
SELECT id, status, (quality_report->>'overall_confidence')::float AS confidence
FROM conversion_jobs
WHERE (quality_report->>'overall_confidence')::float < 90
ORDER BY created_at DESC;
```

**Count jobs that met fidelity targets:**

```sql
SELECT
  COUNT(*) FILTER (WHERE quality_report->'fidelity_targets'->'complex_elements'->>'met' = 'true') AS complex_met,
  COUNT(*) FILTER (WHERE quality_report->'fidelity_targets'->'text_based'->>'met' = 'true') AS text_met
FROM conversion_jobs
WHERE quality_report IS NOT NULL;
```

**Find jobs with warnings:**

```sql
SELECT id, status, jsonb_array_length(quality_report->'warnings') AS warning_count
FROM conversion_jobs
WHERE jsonb_array_length(quality_report->'warnings') > 0
ORDER BY warning_count DESC;
```

### Programmatic Usage

```python
from app.services.conversion.quality_scorer import QualityScorer
from app.schemas.quality_report import QualityReport

# Initialize quality scorer
scorer = QualityScorer()

# Prepare data from pipeline
layout_analysis = {
    "pages": page_analyses  # From Story 4.2
}
document_structure = {
    "chapters": chapters,  # From Story 4.3
    "toc": toc
}

# Generate complete quality report
quality_report = scorer.generate_quality_report(
    layout_analysis=layout_analysis,
    document_structure=document_structure
)

# Access results
print(f"Overall Confidence: {quality_report.overall_confidence}%")
print(f"Tables Detected: {quality_report.elements['tables']['count']}")
print(f"Warnings: {len(quality_report.warnings)}")

# Check fidelity targets
if "complex_elements" in quality_report.fidelity_targets:
    target_met = quality_report.fidelity_targets["complex_elements"]["met"]
    print(f"Complex Fidelity Target Met: {target_met}")
```

### Testing

#### Unit Tests

Run comprehensive unit tests:

```bash
pytest tests/unit/services/conversion/test_quality_scorer.py -v
```

**Test Coverage:**
- Confidence calculation (simple vs. complex documents)
- Element counting (tables, images, equations, chapters)
- Warning generation (threshold tests, critical vs. warning)
- Fidelity target validation (complex vs. text documents)
- Schema validation (Pydantic model validation)
- Error handling (missing data, graceful degradation)

#### Integration Tests

```bash
pytest tests/integration/test_quality_scoring.py -v
```

**Test Coverage:**
- Full pipeline integration (calculate_quality_score task)
- Database storage (quality_report JSONB)
- API responses (quality_report in JobDetail)
- Graceful degradation on errors
- Quality metrics accuracy verification

### Performance

- **Quality Calculation:** <1 second (all metrics)
- **Database Update:** <100ms (JSONB upsert)
- **Overhead on Pipeline:** Negligible (<2% total conversion time)

### Error Handling

#### Graceful Degradation Strategy

If quality scoring fails (AI error, missing data, etc.), the system:

1. **Logs Error:** Full stack trace for debugging
2. **Saves Degraded Report:** Returns minimal quality report:
   ```json
   {
     "overall_confidence": null,
     "elements": {},
     "warnings": ["Quality scoring unavailable due to error"],
     "fidelity_targets": {}
   }
   ```
3. **Continues Pipeline:** EPUB generation not blocked by quality scoring failures
4. **Returns Success:** Job marked as COMPLETED with degraded quality report

#### Example Error Handling

```python
try:
    scorer = QualityScorer()
    quality_report = scorer.generate_quality_report(layout_analysis, document_structure)
except Exception as e:
    logger.error(f"Quality scoring failed: {str(e)}", exc_info=True)
    # Return degraded report - don't block pipeline
    quality_report = {
        "overall_confidence": None,
        "elements": {},
        "warnings": [f"Quality scoring error: {str(e)}"],
        "fidelity_targets": {}
    }
```

### Troubleshooting

#### Quality Report Missing from API Response

**Solutions:**
1. Check `quality_report` column exists in database (run migration 007)
2. Verify quality scoring ran (check logs for "Quality report generated")
3. Check `QUALITY_SCORING_ENABLED=true` in `.env`

#### All Confidence Scores are 99%

**Cause:** Document has no complex elements (tables, equations) - all text
**Expected:** Text-based documents default to 99% confidence

#### Warnings Generated for High-Quality Document

**Solutions:**
1. Check warning threshold: `QUALITY_WARNING_THRESHOLD=80`
2. Lower threshold if too many false positives: `QUALITY_WARNING_THRESHOLD=70`
3. Review AI confidence scores in `layout_analysis` column

#### Fidelity Target Always "Not Met"

**Solutions:**
1. Verify target thresholds:
   - Complex: `QUALITY_TARGET_COMPLEX=95`
   - Text: `QUALITY_TARGET_TEXT=99`
2. Adjust targets if unrealistic for your PDF types
3. Review actual confidence scores in quality report

### Best Practices

1. **Monitor Quality Reports:** Regularly review quality reports to identify patterns in low-confidence documents
2. **Adjust Thresholds:** Tune warning thresholds based on your document types and quality standards
3. **User Communication:** Display quality warnings prominently in UI for manual review
4. **Analytics:** Track fidelity target achievement rates to measure AI model performance over time
5. **Continuous Improvement:** Use low-confidence examples to improve AI prompts or model selection

---

**Last Updated:** 2025-12-13
**Maintained by:** xavier
**Questions:** See project documentation or GitHub issues

---