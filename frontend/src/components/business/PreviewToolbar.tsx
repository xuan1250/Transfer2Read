'use client';

import { Job } from '@/types/job';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  ArrowLeft,
  Download,
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  ToggleLeft,
  ToggleRight,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface PreviewToolbarProps {
  job: Job;
  isSyncEnabled: boolean;
  onSyncToggle: () => void;
  zoomLevel: 'fit-width' | 'fit-page' | 100 | 150 | 200;
  onZoomChange: (zoom: 'fit-width' | 'fit-page' | 100 | 150 | 200) => void;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onBackToResults: () => void;
  onDownload: () => void;
  isMobile: boolean;
}

/**
 * PreviewToolbar Component
 *
 * Navigation toolbar for split-screen preview.
 * Features:
 * - Job title/filename display
 * - Sync toggle button
 * - Zoom controls (PDF pane)
 * - Page navigation controls
 * - Back to Results button
 * - Download EPUB button
 * - Keyboard shortcuts support
 *
 * AC #7: Navigation and Controls
 */
export default function PreviewToolbar({
  job,
  isSyncEnabled,
  onSyncToggle,
  zoomLevel,
  onZoomChange,
  currentPage,
  totalPages,
  onPageChange,
  onBackToResults,
  onDownload,
  isMobile,
}: PreviewToolbarProps) {
  const handleZoomIn = () => {
    if (zoomLevel === 'fit-width' || zoomLevel === 'fit-page') {
      onZoomChange(100);
    } else if (zoomLevel === 100) {
      onZoomChange(150);
    } else if (zoomLevel === 150) {
      onZoomChange(200);
    }
  };

  const handleZoomOut = () => {
    if (zoomLevel === 200) {
      onZoomChange(150);
    } else if (zoomLevel === 150) {
      onZoomChange(100);
    } else if (zoomLevel === 100) {
      onZoomChange('fit-width');
    }
  };

  const handleFitWidth = () => {
    onZoomChange('fit-width');
  };

  const handleFitPage = () => {
    onZoomChange('fit-page');
  };

  const goToPrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  return (
    <TooltipProvider>
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
          {/* Left: Back button and title */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onBackToResults}
                  aria-label="Back to results (Esc)"
                >
                  <ArrowLeft className="h-4 w-4" />
                  {!isMobile && <span className="ml-2">Back</span>}
                </Button>
              </TooltipTrigger>
              <TooltipContent>Back to Results (Esc)</TooltipContent>
            </Tooltip>

            <div className="truncate">
              <h1 className="text-sm font-semibold text-gray-900 truncate">
                {job.original_filename || `Job ${job.id.slice(0, 8)}`}
              </h1>
              <p className="text-xs text-gray-500">Preview Comparison</p>
            </div>
          </div>

          {/* Center: Navigation and controls (desktop only) */}
          {!isMobile && (
            <div className="flex items-center gap-2">
              {/* Page Navigation */}
              <div className="flex items-center gap-1 border-r border-gray-200 pr-3">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={goToPrevPage}
                      disabled={currentPage <= 1}
                      aria-label="Previous page (←)"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Previous Page (←)</TooltipContent>
                </Tooltip>

                <span className="text-sm text-gray-600 min-w-[80px] text-center">
                  {currentPage} / {totalPages}
                </span>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={goToNextPage}
                      disabled={currentPage >= totalPages}
                      aria-label="Next page (→)"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Next Page (→)</TooltipContent>
                </Tooltip>
              </div>

              {/* Zoom Controls */}
              <div className="flex items-center gap-1 border-r border-gray-200 pr-3">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleZoomOut}
                      disabled={zoomLevel === 'fit-width'}
                      aria-label="Zoom out (-)"
                    >
                      <ZoomOut className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Zoom Out (-)</TooltipContent>
                </Tooltip>

                <span className="text-sm text-gray-600 min-w-[80px] text-center">
                  {typeof zoomLevel === 'number' ? `${zoomLevel}%` : zoomLevel}
                </span>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleZoomIn}
                      disabled={zoomLevel === 200}
                      aria-label="Zoom in (+)"
                    >
                      <ZoomIn className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Zoom In (+)</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={zoomLevel === 'fit-width' ? 'secondary' : 'ghost'}
                      size="sm"
                      onClick={handleFitWidth}
                      aria-label="Fit width"
                    >
                      <Maximize2 className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Fit Width</TooltipContent>
                </Tooltip>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={zoomLevel === 'fit-page' ? 'secondary' : 'ghost'}
                      size="sm"
                      onClick={handleFitPage}
                      aria-label="Fit page"
                    >
                      <Minimize2 className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Fit Page</TooltipContent>
                </Tooltip>
              </div>

              {/* Sync Toggle */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={isSyncEnabled ? 'default' : 'outline'}
                    size="sm"
                    onClick={onSyncToggle}
                    aria-label="Toggle synchronization (S)"
                    className="gap-2"
                  >
                    {isSyncEnabled ? (
                      <ToggleRight className="h-4 w-4" />
                    ) : (
                      <ToggleLeft className="h-4 w-4" />
                    )}
                    <span className="text-xs">Sync</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Toggle Sync (S)</TooltipContent>
              </Tooltip>
            </div>
          )}

          {/* Right: Download button */}
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="default"
                  size="sm"
                  onClick={onDownload}
                  className="gap-2"
                  aria-label="Download EPUB"
                >
                  <Download className="h-4 w-4" />
                  {!isMobile && <span>Download</span>}
                </Button>
              </TooltipTrigger>
              <TooltipContent>Download EPUB</TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Keyboard shortcuts hint (desktop only) */}
        {!isMobile && (
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Keyboard: <kbd className="px-1 bg-white border border-gray-300 rounded">←/→</kbd> Navigate
              {' • '}
              <kbd className="px-1 bg-white border border-gray-300 rounded">+/-</kbd> Zoom
              {' • '}
              <kbd className="px-1 bg-white border border-gray-300 rounded">S</kbd> Sync
              {' • '}
              <kbd className="px-1 bg-white border border-gray-300 rounded">Esc</kbd> Back
            </p>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
