import { describe, it, expect } from 'vitest';
import {
  pdfPageToEpubLocation,
  epubLocationToPdfPage,
  getChapterMapping,
  debounce,
  ChapterMapping,
} from './scroll-utils';
import type { QualityReport } from '@/types/job';

/**
 * Unit Tests for Scroll Synchronization Utilities
 *
 * Tests the PDF ↔ EPUB mapping logic for split-screen synchronization.
 * Covers:
 * - pdfPageToEpubLocation: PDF page → EPUB chapter + progress
 * - epubLocationToPdfPage: EPUB chapter + progress → PDF page
 * - getChapterMapping: Extract mapping from quality report
 * - debounce: Utility function for performance optimization
 */

describe('scroll-utils', () => {
  // Sample chapter mapping for testing
  const mockChapterMapping: ChapterMapping[] = [
    { chapter_id: 1, title: 'Introduction', pdf_page_start: 1, pdf_page_end: 5 },
    { chapter_id: 2, title: 'Chapter 1', pdf_page_start: 6, pdf_page_end: 25 },
    { chapter_id: 3, title: 'Chapter 2', pdf_page_start: 26, pdf_page_end: 50 },
    { chapter_id: 4, title: 'Conclusion', pdf_page_start: 51, pdf_page_end: 55 },
  ];

  describe('pdfPageToEpubLocation', () => {
    it('should map PDF page to correct chapter and progress at start', () => {
      // Page 1 is at the start of chapter 1
      const result = pdfPageToEpubLocation(1, mockChapterMapping);
      expect(result.chapterId).toBe(1);
      expect(result.progress).toBe(0); // 0% through chapter (first page)
    });

    it('should map PDF page to correct chapter and progress at end', () => {
      // Page 5 is at the end of chapter 1 (pages 1-5)
      const result = pdfPageToEpubLocation(5, mockChapterMapping);
      expect(result.chapterId).toBe(1);
      expect(result.progress).toBe(0.8); // 80% through chapter (4/5)
    });

    it('should map PDF page to correct chapter and progress in middle', () => {
      // Page 15 in chapter 2 (pages 6-25)
      // Progress = (15 - 6) / (25 - 6 + 1) = 9 / 20 = 0.45
      const result = pdfPageToEpubLocation(15, mockChapterMapping);
      expect(result.chapterId).toBe(2);
      expect(result.progress).toBeCloseTo(0.45, 2);
    });

    it('should handle PDF page at chapter boundary (start of new chapter)', () => {
      // Page 26 is the first page of chapter 3
      const result = pdfPageToEpubLocation(26, mockChapterMapping);
      expect(result.chapterId).toBe(3);
      expect(result.progress).toBe(0); // Start of chapter
    });

    it('should handle PDF page at chapter boundary (end of previous chapter)', () => {
      // Page 25 is the last page of chapter 2 (pages 6-25, total 20 pages)
      // Progress = (25 - 6) / (25 - 6 + 1) = 19 / 20 = 0.95
      const result = pdfPageToEpubLocation(25, mockChapterMapping);
      expect(result.chapterId).toBe(2);
      expect(result.progress).toBe(0.95); // 95% through chapter (page 20 of 20)
    });

    it('should default to first chapter if PDF page not found', () => {
      // Page 100 doesn't exist in mapping
      const result = pdfPageToEpubLocation(100, mockChapterMapping);
      expect(result.chapterId).toBe(1);
      expect(result.progress).toBe(0);
    });

    it('should default to first chapter for page 0', () => {
      const result = pdfPageToEpubLocation(0, mockChapterMapping);
      expect(result.chapterId).toBe(1);
      expect(result.progress).toBe(0);
    });

    it('should clamp progress to [0, 1] range', () => {
      // Edge case: ensure progress never exceeds 1.0
      const result = pdfPageToEpubLocation(5, mockChapterMapping);
      expect(result.progress).toBeLessThanOrEqual(1);
      expect(result.progress).toBeGreaterThanOrEqual(0);
    });
  });

  describe('epubLocationToPdfPage', () => {
    it('should map EPUB chapter start to correct PDF page', () => {
      // Chapter 2 starts at PDF page 6
      const result = epubLocationToPdfPage(2, 0, mockChapterMapping);
      expect(result).toBe(6);
    });

    it('should map EPUB chapter end to correct PDF page', () => {
      // Chapter 2 ends at PDF page 25
      const result = epubLocationToPdfPage(2, 1, mockChapterMapping);
      expect(result).toBe(25);
    });

    it('should map EPUB chapter middle to correct PDF page', () => {
      // Chapter 2, 50% progress → Page 15-16 (mid-point between 6-25)
      const result = epubLocationToPdfPage(2, 0.5, mockChapterMapping);
      expect(result).toBeGreaterThanOrEqual(15);
      expect(result).toBeLessThanOrEqual(16);
    });

    it('should handle progress = 0 (chapter start)', () => {
      const result = epubLocationToPdfPage(3, 0, mockChapterMapping);
      expect(result).toBe(26); // Chapter 3 starts at page 26
    });

    it('should handle progress = 1 (chapter end)', () => {
      const result = epubLocationToPdfPage(3, 1, mockChapterMapping);
      expect(result).toBe(50); // Chapter 3 ends at page 50
    });

    it('should default to page 1 if chapter not found', () => {
      const result = epubLocationToPdfPage(99, 0.5, mockChapterMapping);
      expect(result).toBe(1);
    });

    it('should clamp result to chapter bounds', () => {
      // Progress > 1 should still return last page of chapter
      const result = epubLocationToPdfPage(1, 1.5, mockChapterMapping);
      expect(result).toBeLessThanOrEqual(5); // Chapter 1 ends at page 5
      expect(result).toBeGreaterThanOrEqual(1);
    });
  });

  describe('round-trip conversion (PDF → EPUB → PDF)', () => {
    it('should preserve PDF page after round-trip at chapter start', () => {
      const originalPage = 6; // Start of chapter 2
      const epubLocation = pdfPageToEpubLocation(originalPage, mockChapterMapping);
      const resultPage = epubLocationToPdfPage(
        epubLocation.chapterId,
        epubLocation.progress,
        mockChapterMapping
      );
      expect(resultPage).toBe(originalPage);
    });

    it('should preserve PDF page after round-trip in middle of chapter', () => {
      const originalPage = 15; // Middle of chapter 2
      const epubLocation = pdfPageToEpubLocation(originalPage, mockChapterMapping);
      const resultPage = epubLocationToPdfPage(
        epubLocation.chapterId,
        epubLocation.progress,
        mockChapterMapping
      );
      // Allow ±1 page tolerance due to rounding
      expect(Math.abs(resultPage - originalPage)).toBeLessThanOrEqual(1);
    });
  });

  describe('getChapterMapping', () => {
    it('should extract chapter mapping from quality report', () => {
      const mockQualityReport: Partial<QualityReport> = {
        elements: {
          paragraphs: { count: 100, avg_confidence: 0.95 },
          headings: { count: 10, avg_confidence: 0.98 },
          tables: { count: 5, avg_confidence: 0.85 },
          images: { count: 8, avg_confidence: 0.92 },
          equations: { count: 0, avg_confidence: 0 },
          chapters: {
            count: 4,
            avg_confidence: 0.96,
            mapping: mockChapterMapping,
          },
        },
      };

      const result = getChapterMapping(mockQualityReport as QualityReport);
      expect(result).toEqual(mockChapterMapping);
      expect(result).toHaveLength(4);
    });

    it('should return empty array if quality report is undefined', () => {
      const result = getChapterMapping(undefined);
      expect(result).toEqual([]);
    });

    it('should return empty array if elements is undefined', () => {
      const mockQualityReport: Partial<QualityReport> = {};
      const result = getChapterMapping(mockQualityReport as QualityReport);
      expect(result).toEqual([]);
    });

    it('should return empty array if chapters mapping is undefined', () => {
      const mockQualityReport: Partial<QualityReport> = {
        elements: {
          paragraphs: { count: 100, avg_confidence: 0.95 },
          headings: { count: 10, avg_confidence: 0.98 },
          tables: { count: 5, avg_confidence: 0.85 },
          images: { count: 8, avg_confidence: 0.92 },
          equations: { count: 0, avg_confidence: 0 },
          chapters: {
            count: 0,
            avg_confidence: 0,
          },
        },
      };
      const result = getChapterMapping(mockQualityReport as QualityReport);
      expect(result).toEqual([]);
    });
  });

  describe('debounce', () => {
    it('should debounce function calls', (done) => {
      let callCount = 0;
      const fn = () => {
        callCount++;
      };
      const debouncedFn = debounce(fn, 100);

      // Call multiple times rapidly
      debouncedFn();
      debouncedFn();
      debouncedFn();

      // Should not have called yet
      expect(callCount).toBe(0);

      // Wait for debounce delay
      setTimeout(() => {
        // Should have called only once
        expect(callCount).toBe(1);
        done();
      }, 150);
    });

    it('should pass arguments correctly', (done) => {
      let receivedArgs: unknown[] = [];
      const fn = (...args: unknown[]) => {
        receivedArgs = args;
      };
      const debouncedFn = debounce(fn, 100);

      debouncedFn('test', 123, { key: 'value' });

      setTimeout(() => {
        expect(receivedArgs).toEqual(['test', 123, { key: 'value' }]);
        done();
      }, 150);
    });

    it('should reset timer on subsequent calls', (done) => {
      let callCount = 0;
      const fn = () => {
        callCount++;
      };
      const debouncedFn = debounce(fn, 100);

      debouncedFn();

      // Call again after 50ms (before first timeout completes)
      setTimeout(() => {
        debouncedFn();
      }, 50);

      // Check at 120ms (50ms + 70ms < 150ms total)
      setTimeout(() => {
        // Should not have called yet (timer was reset)
        expect(callCount).toBe(0);
      }, 120);

      // Check at 200ms (should have called once)
      setTimeout(() => {
        expect(callCount).toBe(1);
        done();
      }, 200);
    });

    it('should use default delay of 200ms', (done) => {
      let callCount = 0;
      const fn = () => {
        callCount++;
      };
      const debouncedFn = debounce(fn); // No delay specified

      debouncedFn();

      // Should not have called at 150ms
      setTimeout(() => {
        expect(callCount).toBe(0);
      }, 150);

      // Should have called at 250ms
      setTimeout(() => {
        expect(callCount).toBe(1);
        done();
      }, 250);
    });
  });
});
