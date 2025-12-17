import { QualityReport } from '@/types/job';

/**
 * Chapter Mapping Interface
 * Represents a chapter's PDF page range from quality_report
 */
export interface ChapterMapping {
  chapter_id: number;
  title: string;
  pdf_page_start: number;
  pdf_page_end: number;
}

/**
 * EPUB Location Interface
 * Represents a location in the EPUB (chapter + relative progress)
 */
export interface EpubLocation {
  chapterId: number;
  progress: number; // 0.0 to 1.0 (relative position within chapter)
}

/**
 * Maps PDF page number to EPUB location
 *
 * Algorithm:
 * 1. Find chapter containing the PDF page
 * 2. Calculate relative progress within that chapter
 * 3. Return chapter ID and progress
 *
 * @param pdfPage - Current PDF page number (1-indexed)
 * @param chapterMapping - Chapter-to-page mapping from quality_report
 * @returns EPUB location (chapter ID + progress within chapter)
 *
 * Example:
 * - PDF page 15, chapter 2 spans pages 11-25
 * - Progress = (15 - 11) / (25 - 11) = 4/14 ≈ 0.286 (28.6% through chapter)
 * - Returns: { chapterId: 2, progress: 0.286 }
 */
export function pdfPageToEpubLocation(
  pdfPage: number,
  chapterMapping: ChapterMapping[]
): EpubLocation {
  // Find chapter containing current PDF page
  const chapter = chapterMapping.find(
    (ch) => pdfPage >= ch.pdf_page_start && pdfPage <= ch.pdf_page_end
  );

  // If no chapter found (edge case), default to first chapter at beginning
  if (!chapter) {
    return { chapterId: 1, progress: 0 };
  }

  // Calculate relative progress within chapter
  const chapterLength = chapter.pdf_page_end - chapter.pdf_page_start + 1;
  const pageWithinChapter = pdfPage - chapter.pdf_page_start;
  const progress = pageWithinChapter / chapterLength;

  return {
    chapterId: chapter.chapter_id,
    progress: Math.max(0, Math.min(1, progress)), // Clamp to [0, 1]
  };
}

/**
 * Maps EPUB location (chapter + progress) back to PDF page number
 *
 * Reverse algorithm:
 * 1. Find chapter by ID
 * 2. Calculate PDF page based on progress within chapter
 * 3. Return page number
 *
 * @param chapterId - EPUB chapter ID
 * @param progress - Relative progress within chapter (0.0 to 1.0)
 * @param chapterMapping - Chapter-to-page mapping from quality_report
 * @returns PDF page number (1-indexed)
 *
 * Example:
 * - Chapter 2, progress 0.286, chapter spans PDF pages 11-25
 * - Page = 11 + (0.286 * (25 - 11)) = 11 + 4 = 15
 */
export function epubLocationToPdfPage(
  chapterId: number,
  progress: number,
  chapterMapping: ChapterMapping[]
): number {
  // Find chapter by ID
  const chapter = chapterMapping.find((ch) => ch.chapter_id === chapterId);

  // If no chapter found, default to page 1
  if (!chapter) {
    return 1;
  }

  // Calculate PDF page based on progress
  const chapterLength = chapter.pdf_page_end - chapter.pdf_page_start + 1;
  const pageOffset = Math.round(progress * chapterLength);
  const pdfPage = chapter.pdf_page_start + pageOffset;

  // Ensure page is within chapter bounds
  return Math.max(
    chapter.pdf_page_start,
    Math.min(chapter.pdf_page_end, pdfPage)
  );
}

/**
 * Extracts chapter mapping from quality report
 *
 * @param qualityReport - Job quality report containing chapter metadata
 * @returns Array of chapter mappings, or empty array if unavailable
 */
export function getChapterMapping(
  qualityReport?: QualityReport
): ChapterMapping[] {
  if (!qualityReport?.elements?.chapters?.mapping) {
    return [];
  }

  return qualityReport.elements.chapters.mapping;
}

/**
 * Debounces a function call
 *
 * Used to optimize scroll synchronization performance by limiting
 * how often sync calculations run during rapid scrolling.
 *
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds (default: 200ms)
 * @returns Debounced function
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number = 200
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function debounced(...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };
}
