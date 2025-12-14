"""
Font Manager Service

Handles font detection, downloading, and embedding for multi-language EPUB support.
Supports EN, ZH, JP, KO, VI languages with CJK character rendering.

Story 4.4: EPUB Generation from AI-Analyzed Content (AC: #4)
"""

from typing import Dict, List, Optional, Set
from pathlib import Path
import re
import logging
import requests
from io import BytesIO

from ebooklib import epub

logger = logging.getLogger(__name__)

# Font URLs from Google Fonts (Noto Sans CJK subset)
FONT_URLS = {
    'noto-sans-sc': 'https://fonts.gstatic.com/s/notosanssc/v36/k3kCo84MPvpLmixcA63oeALhL4iJ-Q7m8w.woff2',  # Simplified Chinese
    'noto-sans-tc': 'https://fonts.gstatic.com/s/notosanstc/v35/k3kCo84MPvpLmixcA63oeALZLYiJ-Q7m8w.woff2',  # Traditional Chinese
    'noto-sans-jp': 'https://fonts.gstatic.com/s/notosansjp/v53/k3kCo84MPvpLmixcA63oeAL5NYiJ-Q7m8w.woff2',  # Japanese
    'noto-sans-kr': 'https://fonts.gstatic.com/s/notosanskr/v36/PbyxFmXiEBPT4ITbgNA5Cgms3VYcOA-vvnIzzuoyeLTq8A.woff2',  # Korean
}

# CJK character ranges for detection
CJK_RANGES = {
    'zh': (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    'zh-cn': (0x4E00, 0x9FFF),
    'zh-tw': (0x4E00, 0x9FFF),
    'ja': (0x3040, 0x309F, 0x30A0, 0x30FF, 0x4E00, 0x9FFF),  # Hiragana + Katakana + Kanji
    'ko': (0xAC00, 0xD7AF),  # Hangul
    'vi': (0x1EA0, 0x1EF9),  # Vietnamese with diacritics
}


class FontManager:
    """
    Manages font detection, downloading, and embedding for EPUB files.

    Features:
    - Detect required fonts based on language and text content
    - Download fonts from Google Fonts API
    - Cache fonts locally to avoid re-downloading
    - Embed fonts in EPUB package
    - Generate CSS @font-face rules

    Usage:
        font_manager = FontManager()
        fonts = font_manager.detect_and_embed_fonts(book, language='zh', text_sample=content)
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize font manager.

        Args:
            cache_dir: Directory to cache downloaded fonts (default: /tmp/epub_fonts)
        """
        self.cache_dir = cache_dir or Path("/tmp/epub_fonts")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._font_cache: Dict[str, bytes] = {}

    def detect_required_fonts(self, language: str, text_sample: str = "") -> List[str]:
        """
        Detect which fonts are needed based on language and text content.

        Args:
            language: Primary language code (en, zh, ja, ko, vi)
            text_sample: Sample text to analyze for special characters

        Returns:
            List of font keys needed (e.g., ['noto-sans-sc', 'noto-sans-jp'])
        """
        required_fonts: Set[str] = set()

        # Map language to font
        language_lower = language.lower()

        if language_lower in ['zh', 'zh-cn', 'zh-hans']:
            required_fonts.add('noto-sans-sc')  # Simplified Chinese
        elif language_lower in ['zh-tw', 'zh-hant']:
            required_fonts.add('noto-sans-tc')  # Traditional Chinese
        elif language_lower == 'ja':
            required_fonts.add('noto-sans-jp')  # Japanese
        elif language_lower == 'ko':
            required_fonts.add('noto-sans-kr')  # Korean

        # Detect CJK characters in text sample if provided
        if text_sample:
            if self._contains_cjk_chars(text_sample, 'zh'):
                required_fonts.add('noto-sans-sc')
            if self._contains_cjk_chars(text_sample, 'ja'):
                required_fonts.add('noto-sans-jp')
            if self._contains_cjk_chars(text_sample, 'ko'):
                required_fonts.add('noto-sans-kr')

        return list(required_fonts)

    def _contains_cjk_chars(self, text: str, lang: str) -> bool:
        """
        Check if text contains CJK characters for specific language.

        Args:
            text: Text to analyze
            lang: Language code (zh, ja, ko, vi)

        Returns:
            True if CJK characters found
        """
        if lang not in CJK_RANGES:
            return False

        ranges = CJK_RANGES[lang]

        # Check if any character falls in CJK range
        for char in text[:1000]:  # Sample first 1000 chars for performance
            char_code = ord(char)

            # Handle tuple of multiple ranges (like Japanese)
            if len(ranges) > 2:
                # Iterate through pairs of (start, end)
                for i in range(0, len(ranges), 2):
                    range_start = ranges[i]
                    range_end = ranges[i + 1]
                    if range_start <= char_code <= range_end:
                        return True
            else:
                # Single range
                range_start, range_end = ranges
                if range_start <= char_code <= range_end:
                    return True

        return False

    def download_font(self, font_key: str) -> Optional[bytes]:
        """
        Download font from Google Fonts or load from cache.

        Args:
            font_key: Font identifier (e.g., 'noto-sans-sc')

        Returns:
            Font file bytes, or None if download fails
        """
        # Check memory cache first
        if font_key in self._font_cache:
            logger.info(f"Font {font_key} loaded from memory cache")
            return self._font_cache[font_key]

        # Check disk cache
        cache_path = self.cache_dir / f"{font_key}.woff2"
        if cache_path.exists():
            try:
                font_bytes = cache_path.read_bytes()
                self._font_cache[font_key] = font_bytes
                logger.info(f"Font {font_key} loaded from disk cache: {cache_path}")
                return font_bytes
            except Exception as e:
                logger.warning(f"Failed to read cached font {font_key}: {e}")

        # Download font
        if font_key not in FONT_URLS:
            logger.error(f"Unknown font key: {font_key}")
            return None

        url = FONT_URLS[font_key]

        try:
            logger.info(f"Downloading font {font_key} from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            font_bytes = response.content

            # Cache to disk
            try:
                cache_path.write_bytes(font_bytes)
                logger.info(f"Font {font_key} cached to disk: {cache_path}")
            except Exception as e:
                logger.warning(f"Failed to cache font {font_key} to disk: {e}")

            # Cache to memory
            self._font_cache[font_key] = font_bytes

            return font_bytes

        except Exception as e:
            logger.error(f"Failed to download font {font_key}: {e}")
            return None

    def embed_fonts_in_epub(
        self,
        book: epub.EpubBook,
        font_keys: List[str]
    ) -> int:
        """
        Embed font files in EPUB package.

        Args:
            book: EPUB book instance
            font_keys: List of font keys to embed

        Returns:
            Number of fonts successfully embedded
        """
        embedded_count = 0

        for font_key in font_keys:
            font_bytes = self.download_font(font_key)

            if not font_bytes:
                logger.warning(f"Skipping font {font_key} - download failed")
                continue

            # Create font item for EPUB
            font_filename = f"fonts/{font_key}.woff2"
            font_item = epub.EpubItem(
                uid=f"font-{font_key}",
                file_name=font_filename,
                media_type="font/woff2",
                content=font_bytes
            )

            book.add_item(font_item)
            embedded_count += 1
            logger.info(f"Embedded font {font_key} in EPUB at {font_filename}")

        return embedded_count

    def generate_font_face_css(self, font_keys: List[str]) -> str:
        """
        Generate CSS @font-face rules for embedded fonts.

        Args:
            font_keys: List of font keys to generate CSS for

        Returns:
            CSS string with @font-face rules
        """
        css_rules = []

        font_family_map = {
            'noto-sans-sc': 'Noto Sans SC',
            'noto-sans-tc': 'Noto Sans TC',
            'noto-sans-jp': 'Noto Sans JP',
            'noto-sans-kr': 'Noto Sans KR',
        }

        for font_key in font_keys:
            if font_key not in font_family_map:
                continue

            family_name = font_family_map[font_key]
            font_path = f"../fonts/{font_key}.woff2"

            css_rule = f"""
@font-face {{
    font-family: '{family_name}';
    src: url('{font_path}') format('woff2');
    font-weight: normal;
    font-style: normal;
    font-display: swap;
}}
"""
            css_rules.append(css_rule.strip())

        return "\n\n".join(css_rules)

    def update_css_with_fonts(self, existing_css: str, font_keys: List[str]) -> str:
        """
        Update existing CSS stylesheet with @font-face rules.

        Args:
            existing_css: Current CSS content
            font_keys: List of font keys to add

        Returns:
            Updated CSS with font-face rules prepended
        """
        font_css = self.generate_font_face_css(font_keys)

        # Prepend font-face rules to existing CSS
        updated_css = f"""/* Multi-Language Font Embedding */
{font_css}

/* Original Stylesheet */
{existing_css}
"""
        return updated_css

    def detect_and_embed_fonts(
        self,
        book: epub.EpubBook,
        language: str,
        text_sample: str = ""
    ) -> Dict[str, any]:
        """
        Detect required fonts, download, and embed in EPUB.

        This is the main convenience method that:
        1. Detects required fonts
        2. Downloads fonts
        3. Embeds in EPUB package
        4. Returns metadata

        Args:
            book: EPUB book instance
            language: Primary language code
            text_sample: Sample text for font detection

        Returns:
            Dict with embedded_fonts list and embedded_count
        """
        # Detect required fonts
        required_fonts = self.detect_required_fonts(language, text_sample)

        if not required_fonts:
            logger.info("No special fonts required for this document")
            return {'embedded_fonts': [], 'embedded_count': 0}

        logger.info(f"Detected required fonts: {required_fonts}")

        # Embed fonts
        embedded_count = self.embed_fonts_in_epub(book, required_fonts)

        return {
            'embedded_fonts': required_fonts,
            'embedded_count': embedded_count
        }
