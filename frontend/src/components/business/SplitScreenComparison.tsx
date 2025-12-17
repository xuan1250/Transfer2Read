'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Job } from '@/types/job';
import { createClient } from '@/lib/supabase/client';
import PDFViewer from './PDFViewer';
import EPUBViewer from './EPUBViewer';
import PreviewToolbar from './PreviewToolbar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface SplitScreenComparisonProps {
  job: Job;
}

/**
 * SplitScreenComparison Component
 *
 * Main component for split-screen PDF/EPUB comparison view.
 * Handles:
 * - Responsive layout (desktop: side-by-side, tablet: vertical stack, mobile: tabs)
 * - File loading from Supabase Storage signed URLs
 * - Scroll synchronization between PDF and EPUB panes
 * - Navigation toolbar with controls
 * - Loading and error states
 *
 * AC #1, #6: Split-screen layout with responsive adaptation
 */
export default function SplitScreenComparison({ job }: SplitScreenComparisonProps) {
  const router = useRouter();
  const supabase = createClient();

  // View state
  const [isSyncEnabled, setIsSyncEnabled] = useState(true);
  const [currentPdfPage, setCurrentPdfPage] = useState(1);
  const [totalPdfPages, setTotalPdfPages] = useState(0);
  const [currentEpubLocation, setCurrentEpubLocation] = useState('');
  const [zoomLevel, setZoomLevel] = useState<'fit-width' | 'fit-page' | 100 | 150 | 200>('fit-width');

  // File URLs state
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [epubUrl, setEpubUrl] = useState<string | null>(null);
  const [filesLoading, setFilesLoading] = useState(true);
  const [filesError, setFilesError] = useState<string | null>(null);

  // Responsive state
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [mobileTab, setMobileTab] = useState<'pdf' | 'epub'>('pdf');

  // Detect screen size
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 1024);
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // Fetch signed URLs for PDF and EPUB
  useEffect(() => {
    const fetchFileUrls = async () => {
      setFilesLoading(true);
      setFilesError(null);

      try {
        // Get auth session
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError || !session) {
          throw new Error('Authentication required. Please log in again.');
        }

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const authHeader = `Bearer ${session.access_token}`;

        // Fetch PDF signed URL
        const pdfResponse = await fetch(`${apiUrl}/api/v1/jobs/${job.id}/files/input`, {
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
          },
        });

        if (!pdfResponse.ok) {
          const errorText = await pdfResponse.text();
          throw new Error(`Failed to fetch PDF file: ${pdfResponse.status} ${errorText}`);
        }

        const pdfData = await pdfResponse.json();
        setPdfUrl(pdfData.download_url || pdfData.url);

        // Fetch EPUB signed URL
        const epubResponse = await fetch(`${apiUrl}/api/v1/jobs/${job.id}/download`, {
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
          },
        });

        if (!epubResponse.ok) {
          const errorText = await epubResponse.text();
          throw new Error(`Failed to fetch EPUB file: ${epubResponse.status} ${errorText}`);
        }

        const epubData = await epubResponse.json();
        setEpubUrl(epubData.download_url || epubData.url);

        setFilesLoading(false);
      } catch (error) {
        console.error('Error fetching file URLs:', error);
        setFilesError(error instanceof Error ? error.message : 'Failed to load files. Please try again.');
        setFilesLoading(false);
      }
    };

    fetchFileUrls();
  }, [job.id, supabase]);

  // Handle file load retry
  const handleRetry = () => {
    setFilesError(null);
    setFilesLoading(true);
    // Trigger re-fetch by forcing component re-mount
    window.location.reload();
  };

  // Handle back to results
  const handleBackToResults = () => {
    router.push(`/jobs/${job.id}`);
  };

  // Handle download EPUB
  const handleDownload = async () => {
    if (epubUrl) {
      window.open(epubUrl, '_blank');
    }
  };

  // Handle zoom change
  const handleZoomChange = (newZoom: 'fit-width' | 'fit-page' | 100 | 150 | 200) => {
    setZoomLevel(newZoom);
  };

  // Handle sync toggle
  const handleSyncToggle = () => {
    setIsSyncEnabled(!isSyncEnabled);
  };

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Arrow keys: Navigate pages (when PDF is focused)
      if (e.key === 'ArrowLeft' && currentPdfPage > 1) {
        setCurrentPdfPage(currentPdfPage - 1);
      } else if (e.key === 'ArrowRight' && currentPdfPage < totalPdfPages) {
        setCurrentPdfPage(currentPdfPage + 1);
      }
      // +/- keys: Zoom
      else if (e.key === '+' || e.key === '=') {
        if (zoomLevel === 'fit-width' || zoomLevel === 'fit-page') {
          setZoomLevel(100);
        } else if (zoomLevel === 100) {
          setZoomLevel(150);
        } else if (zoomLevel === 150) {
          setZoomLevel(200);
        }
      } else if (e.key === '-') {
        if (zoomLevel === 200) {
          setZoomLevel(150);
        } else if (zoomLevel === 150) {
          setZoomLevel(100);
        } else if (zoomLevel === 100) {
          setZoomLevel('fit-width');
        }
      }
      // S key: Toggle sync
      else if (e.key === 's' || e.key === 'S') {
        setIsSyncEnabled(!isSyncEnabled);
      }
      // Esc key: Return to results
      else if (e.key === 'Escape') {
        router.push(`/jobs/${job.id}`);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPdfPage, totalPdfPages, zoomLevel, isSyncEnabled, job.id, router]);

  // Show loading state
  if (filesLoading) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="text-center space-y-4">
            <Skeleton className="h-96 w-full max-w-6xl mx-auto" />
            <p className="text-sm text-gray-500">Loading PDF and EPUB files...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (filesError) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-md w-full space-y-6">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="mt-2">
                {filesError}
              </AlertDescription>
            </Alert>

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleBackToResults}
              >
                Back to Results
              </Button>
              <Button
                variant="default"
                className="flex-1"
                onClick={handleRetry}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Desktop: Side-by-side layout
  const renderDesktopLayout = () => (
    <div className="flex-1 flex flex-row gap-4 p-6 overflow-hidden">
      {/* PDF Pane */}
      <div className="flex-1 bg-gray-100 rounded-lg shadow-sm overflow-hidden">
        <PDFViewer
          pdfUrl={pdfUrl!}
          currentPage={currentPdfPage}
          onPageChange={setCurrentPdfPage}
          onTotalPagesChange={setTotalPdfPages}
          zoomLevel={zoomLevel}
          isSyncEnabled={isSyncEnabled}
          job={job}
        />
      </div>

      {/* EPUB Pane */}
      <div className="flex-1 bg-white rounded-lg shadow-sm overflow-hidden">
        <EPUBViewer
          epubUrl={epubUrl!}
          currentLocation={currentEpubLocation}
          onLocationChange={setCurrentEpubLocation}
          onPdfPageChange={setCurrentPdfPage}
          isSyncEnabled={isSyncEnabled}
          currentPdfPage={currentPdfPage}
          job={job}
        />
      </div>
    </div>
  );

  // Tablet: Vertical stack layout
  const renderTabletLayout = () => (
    <div className="flex-1 flex flex-col gap-4 p-4 overflow-auto">
      {/* PDF Pane */}
      <div className="h-[45vh] bg-gray-100 rounded-lg shadow-sm overflow-hidden">
        <PDFViewer
          pdfUrl={pdfUrl!}
          currentPage={currentPdfPage}
          onPageChange={setCurrentPdfPage}
          onTotalPagesChange={setTotalPdfPages}
          zoomLevel={zoomLevel}
          isSyncEnabled={isSyncEnabled}
          job={job}
        />
      </div>

      {/* EPUB Pane */}
      <div className="h-[45vh] bg-white rounded-lg shadow-sm overflow-hidden">
        <EPUBViewer
          epubUrl={epubUrl!}
          currentLocation={currentEpubLocation}
          onLocationChange={setCurrentEpubLocation}
          onPdfPageChange={setCurrentPdfPage}
          isSyncEnabled={isSyncEnabled}
          currentPdfPage={currentPdfPage}
          job={job}
        />
      </div>
    </div>
  );

  // Mobile: Tabbed view
  const renderMobileLayout = () => (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Tabs value={mobileTab} onValueChange={(value) => setMobileTab(value as 'pdf' | 'epub')} className="flex-1 flex flex-col">
        <div className="px-4 pt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="pdf">PDF</TabsTrigger>
            <TabsTrigger value="epub">EPUB</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="pdf" className="flex-1 mt-4 px-4 pb-4">
          <div className="h-full bg-gray-100 rounded-lg shadow-sm overflow-hidden">
            <PDFViewer
              pdfUrl={pdfUrl!}
              currentPage={currentPdfPage}
              onPageChange={setCurrentPdfPage}
              onTotalPagesChange={setTotalPdfPages}
              zoomLevel={zoomLevel}
              isSyncEnabled={false} // Sync disabled on mobile
              job={job}
            />
          </div>
        </TabsContent>

        <TabsContent value="epub" className="flex-1 mt-4 px-4 pb-4">
          <div className="h-full bg-white rounded-lg shadow-sm overflow-hidden">
            <EPUBViewer
              epubUrl={epubUrl!}
              currentLocation={currentEpubLocation}
              onLocationChange={setCurrentEpubLocation}
              onPdfPageChange={setCurrentPdfPage}
              isSyncEnabled={false} // Sync disabled on mobile
              currentPdfPage={currentPdfPage}
              job={job}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Toolbar */}
      <PreviewToolbar
        job={job}
        isSyncEnabled={isSyncEnabled}
        onSyncToggle={handleSyncToggle}
        zoomLevel={zoomLevel}
        onZoomChange={handleZoomChange}
        currentPage={currentPdfPage}
        totalPages={totalPdfPages}
        onPageChange={setCurrentPdfPage}
        onBackToResults={handleBackToResults}
        onDownload={handleDownload}
        isMobile={isMobile}
      />

      {/* Content Area - Responsive */}
      {isMobile ? renderMobileLayout() : isTablet ? renderTabletLayout() : renderDesktopLayout()}
    </div>
  );
}
