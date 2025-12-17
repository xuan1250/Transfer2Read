'use client';

import { useState, useEffect, useRef } from 'react';
import { ReactReader, ReactReaderStyle } from 'react-reader';
import type { Rendition as IRendition } from 'epubjs';
import { Job } from '@/types/job';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { epubLocationToPdfPage } from '@/lib/scroll-utils';

interface EPUBViewerProps {
  epubUrl: string;
  currentLocation: string;
  onLocationChange: (location: string) => void;
  onPdfPageChange?: (page: number) => void; // Callback for bidirectional sync
  isSyncEnabled: boolean;
  currentPdfPage: number;
  job: Job;
}

/**
 * EPUBViewer Component
 *
 * Renders EPUB using react-reader library (epubjs wrapper).
 * Features:
 * - Native EPUB rendering with proper formatting
 * - Table of contents (TOC) support
 * - CFI location tracking for scroll synchronization
 * - Responsive text reflow
 *
 * AC #3: EPUB Rendering Strategy (Option A: react-reader)
 */
export default function EPUBViewer({
  epubUrl,
  currentLocation,
  onLocationChange,
  onPdfPageChange,
  isSyncEnabled,
  currentPdfPage,
  job,
}: EPUBViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rendition, setRendition] = useState<IRendition | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Custom styles for react-reader
  const readerStyles: typeof ReactReaderStyle = {
    ...ReactReaderStyle,
    reader: {
      ...ReactReaderStyle.reader,
      backgroundColor: '#ffffff',
    },
    tocArea: {
      ...ReactReaderStyle.tocArea,
      backgroundColor: '#f9fafb',
    },
    readerArea: {
      ...ReactReaderStyle.readerArea,
      backgroundColor: '#ffffff',
      transition: undefined, // Remove default transition for smoother sync
    },
  };

  // Handle rendition ready (for customization)
  const handleRenditionReady = (rendition: IRendition) => {
    setRendition(rendition);
    setLoading(false);
    setError(null);

    // Customize EPUB rendering
    rendition.themes.default({
      'font-family': 'system-ui, -apple-system, sans-serif',
      'line-height': '1.6',
      'color': '#1f2937',
    });

    // Listen for errors
    rendition.on('rendered', () => {
      setLoading(false);
    });

    rendition.on('error', (err: Error) => {
      console.error('EPUB rendering error:', err);
      setError('Error rendering EPUB content. The file may be corrupted.');
    });
  };

  // Synchronize EPUB location with PDF page
  useEffect(() => {
    if (!isSyncEnabled || !rendition || !job.quality_report?.elements?.chapters?.mapping) {
      return;
    }

    const chapterMapping = job.quality_report.elements.chapters.mapping;

    // Find chapter containing current PDF page
    const currentChapter = chapterMapping.find(
      (ch) => currentPdfPage >= ch.pdf_page_start && currentPdfPage <= ch.pdf_page_end
    );

    if (currentChapter) {
      // Calculate relative progress within chapter
      const progress = (currentPdfPage - currentChapter.pdf_page_start) /
                       (currentChapter.pdf_page_end - currentChapter.pdf_page_start);

      // Map chapter_id to EPUB spine location
      // epubjs uses spine index (0-based) for navigation
      // Assuming chapter_id maps to spine index (chapter_id - 1)
      const spineIndex = currentChapter.chapter_id - 1;

      // Navigate to the chapter using spine index
      // This will display the chapter corresponding to the PDF page
      if (spineIndex >= 0) {
        try {
          // Display the spine item at the calculated index
          // react-reader will handle the CFI generation internally
          rendition.display(spineIndex).then(() => {
            console.log(`Synced: PDF page ${currentPdfPage} → EPUB Chapter ${currentChapter.chapter_id} (${Math.round(progress * 100)}% through chapter)`);
          }).catch((err: Error) => {
            console.error('Error syncing EPUB location:', err);
          });
        } catch (err) {
          console.error('Error displaying EPUB chapter:', err);
        }
      }
    }
  }, [currentPdfPage, isSyncEnabled, rendition, job.quality_report]);

  // Bidirectional sync: EPUB location change → PDF page
  useEffect(() => {
    if (!rendition) return;

    // Listen for EPUB location changes (user navigating EPUB)
    const handleLocationChanged = (location: { start: { index: number } }) => {
      const spineIndex = location.start.index;

      // Sync EPUB → PDF if sync enabled and mapping available
      if (isSyncEnabled && onPdfPageChange && job.quality_report?.elements?.chapters?.mapping) {
        const chapterMapping = job.quality_report.elements.chapters.mapping;

        // Map spine index to chapter_id (assuming spine index + 1 = chapter_id)
        const chapterId = spineIndex + 1;

        // Find the chapter to get its PDF page range
        const chapter = chapterMapping.find((ch) => ch.chapter_id === chapterId);

        if (chapter) {
          // Navigate to the start of the corresponding PDF chapter
          // Using progress=0 to jump to chapter start
          const pdfPage = epubLocationToPdfPage(chapterId, 0, chapterMapping);
          onPdfPageChange(pdfPage);
          console.log(`Bidirectional sync: EPUB Chapter ${chapterId} → PDF page ${pdfPage}`);
        }
      }
    };

    rendition.on('relocated', handleLocationChanged);

    return () => {
      rendition.off('relocated', handleLocationChanged);
    };
  }, [rendition, isSyncEnabled, onPdfPageChange, job.quality_report]);

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-white">
      {/* EPUB Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-gray-700">Converted EPUB</h3>
          {isSyncEnabled && (
            <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
              Sync Active
            </span>
          )}
        </div>

        {job.quality_report?.overall_confidence && (
          <div className="text-xs text-gray-500">
            Quality: {job.quality_report.overall_confidence}%
          </div>
        )}
      </div>

      {/* EPUB Content */}
      <div className="flex-1 overflow-hidden relative">
        {error ? (
          <div className="p-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        ) : loading ? (
          <div className="p-4 space-y-4">
            <Skeleton className="h-[600px] w-full" />
            <p className="text-sm text-gray-500 text-center">Loading EPUB...</p>
          </div>
        ) : null}

        {/* React Reader */}
        <div className={`h-full ${loading || error ? 'hidden' : ''}`}>
          <ReactReader
            url={epubUrl}
            location={currentLocation}
            locationChanged={onLocationChange}
            getRendition={handleRenditionReady}
            readerStyles={readerStyles}
            epubOptions={{
              flow: 'paginated',
              manager: 'continuous',
              allowScriptedContent: false, // Security: disable scripts in EPUB
            }}
            loadingView={
              <div className="flex items-center justify-center h-full">
                <Skeleton className="h-[600px] w-full max-w-2xl" />
              </div>
            }
          />
        </div>
      </div>
    </div>
  );
}
