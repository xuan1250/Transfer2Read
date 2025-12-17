'use client';

import { useState, useEffect, useRef } from 'react';
import { Job } from '@/types/job';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';

// Dynamic imports for react-pdf to avoid SSR issues
import type { DocumentProps, PageProps } from 'react-pdf';
import type { PDFDocumentProxy } from 'pdfjs-dist';

let Document: React.ComponentType<DocumentProps>;
let Page: React.ComponentType<PageProps>;
let pdfjs: typeof import('pdfjs-dist');

// Import CSS on client side only
if (typeof window !== 'undefined') {
  import('react-pdf/dist/Page/AnnotationLayer.css');
  import('react-pdf/dist/Page/TextLayer.css');
}

interface PDFViewerProps {
  pdfUrl: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  onTotalPagesChange: (total: number) => void;
  zoomLevel: 'fit-width' | 'fit-page' | 100 | 150 | 200;
  isSyncEnabled: boolean;
  job: Job;
}

/**
 * PDFViewer Component
 *
 * Renders PDF using react-pdf library with controls.
 * Features:
 * - Lazy loading for performance
 * - Page navigation (Previous/Next)
 * - Current page indicator
 * - Zoom controls
 * - Smooth scrolling
 *
 * AC #2: PDF Viewer Implementation
 */
export default function PDFViewer({
  pdfUrl,
  currentPage,
  onPageChange,
  onTotalPagesChange,
  zoomLevel,
  isSyncEnabled,
}: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [containerWidth, setContainerWidth] = useState<number>(0);
  const [pdfLoaded, setPdfLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load react-pdf dynamically on client side only
  useEffect(() => {
    const loadPdfJs = async () => {
      try {
        const reactPdf = await import('react-pdf');
        Document = reactPdf.Document;
        Page = reactPdf.Page;
        pdfjs = reactPdf.pdfjs;

        // Configure PDF.js worker
        pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

        setPdfLoaded(true);
      } catch (err) {
        console.error('Error loading PDF.js:', err);
        setError('Failed to initialize PDF viewer. Please refresh the page.');
        setLoading(false);
      }
    };

    loadPdfJs();
  }, []);

  // Measure container width for responsive PDF rendering
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth - 32); // Subtract padding
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Handle PDF load success
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    onTotalPagesChange(numPages);
    setLoading(false);
    setError(null);
  };

  // Handle PDF load error
  const onDocumentLoadError = (error: Error) => {
    console.error('Error loading PDF:', error);
    setError('Failed to load PDF. The file may be corrupted or unavailable.');
    setLoading(false);
  };

  // Calculate page width based on zoom level
  const getPageWidth = () => {
    if (zoomLevel === 'fit-width') {
      return containerWidth;
    } else if (zoomLevel === 'fit-page') {
      return containerWidth * 0.9; // Slightly smaller for fit-page
    } else {
      // Numeric zoom levels (100, 150, 200)
      return (containerWidth * zoomLevel) / 100;
    }
  };

  // Page navigation handlers
  const goToPrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const goToNextPage = () => {
    if (currentPage < numPages) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <div ref={containerRef} className="h-full flex flex-col bg-gray-100">
      {/* PDF Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-gray-700">Original PDF</h3>
          {isSyncEnabled && (
            <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
              Sync Active
            </span>
          )}
        </div>

        {/* Page Navigation */}
        {!loading && !error && (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={goToPrevPage}
              disabled={currentPage <= 1}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            <span className="text-sm text-gray-600">
              Page {currentPage} of {numPages}
            </span>

            <Button
              variant="ghost"
              size="sm"
              onClick={goToNextPage}
              disabled={currentPage >= numPages}
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto p-4">
        {!pdfLoaded ? (
          <div className="flex justify-center">
            <div className="space-y-4">
              <Skeleton className="h-[600px] w-full max-w-2xl" />
              <p className="text-sm text-gray-500 text-center">Initializing PDF viewer...</p>
            </div>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : (
          <div className="flex justify-center">
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="space-y-4">
                  <Skeleton className="h-[600px] w-full max-w-2xl" />
                  <p className="text-sm text-gray-500 text-center">Loading PDF...</p>
                </div>
              }
              error={
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Unable to load PDF. Please try refreshing the page.
                  </AlertDescription>
                </Alert>
              }
            >
              <Page
                pageNumber={currentPage}
                width={getPageWidth()}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                loading={
                  <Skeleton className="h-[600px] w-full" />
                }
              />
            </Document>
          </div>
        )}
      </div>
    </div>
  );
}
