/**
 * QualityReportSummary Component
 *
 * Displays comprehensive quality report after conversion with user-friendly messaging
 */

'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  FileText,
  Table as TableIcon,
  Image as ImageIcon,
  BookOpen,
  Info,
} from 'lucide-react';
import type { QualityReport } from '@/types/job';
import {
  getQualityLevelMessage,
  getQualityEmoji,
  getElementMessage,
  getConfidenceProgressColor,
} from '@/lib/quality-utils';

interface QualityReportSummaryProps {
  qualityReport: QualityReport;
  className?: string;
}

export function QualityReportSummary({ qualityReport, className }: QualityReportSummaryProps) {
  const {
    overall_confidence = 0,
    elements = {},
    warnings = [],
    estimated_cost = 0,
    pages_processed = 0,
  } = qualityReport;

  const qualityMessage = getQualityLevelMessage(overall_confidence);
  const qualityEmoji = getQualityEmoji(overall_confidence);
  const progressColor = getConfidenceProgressColor(overall_confidence);

  // Extract element metrics
  const tables = elements.tables || { count: 0 };
  const images = elements.images || { count: 0 };
  const equations = elements.equations || { count: 0 };
  const chapters = elements.chapters || { count: 0 };

  return (
    <div className={`space-y-6 ${className || ''}`}>
      {/* Overall Quality Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">{qualityEmoji}</span>
            Quality Report
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Quality Level Message */}
          <div className="text-lg font-medium text-foreground">{qualityMessage}</div>

          {/* Confidence Score Progress Bar */}
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm text-muted-foreground">Overall Confidence</span>
              <span className="text-sm font-medium">{Math.round(overall_confidence)}%</span>
            </div>
            <Progress
              value={overall_confidence}
              className="h-3"
              indicatorClassName={progressColor}
            />
          </div>

          {/* Estimated Cost */}
          {estimated_cost > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Processing cost:</span>
              <Badge variant="secondary">${estimated_cost.toFixed(2)}</Badge>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Info className="h-4 w-4 text-muted-foreground" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>AI processing cost based on token usage</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Pages */}
        {pages_processed > 0 && (
          <MetricCard
            icon={<FileText className="h-5 w-5" />}
            label="Pages"
            count={pages_processed}
            message={`${pages_processed} pages processed`}
          />
        )}

        {/* Tables */}
        <MetricCard
          icon={<TableIcon className="h-5 w-5" />}
          label="Tables"
          count={tables.count}
          message={getElementMessage('tables', tables.count, tables.avg_confidence)}
          confidence={tables.avg_confidence}
        />

        {/* Images */}
        <MetricCard
          icon={<ImageIcon className="h-5 w-5" />}
          label="Images"
          count={images.count}
          message={getElementMessage('images', images.count)}
        />

        {/* Equations */}
        <MetricCard
          icon={<span className="text-xl">🧮</span>}
          label="Equations"
          count={equations.count}
          message={getElementMessage('equations', equations.count, equations.avg_confidence)}
          confidence={equations.avg_confidence}
        />

        {/* Chapters */}
        <MetricCard
          icon={<BookOpen className="h-5 w-5" />}
          label="Chapters"
          count={chapters.count}
          message={getElementMessage('chapters', chapters.count)}
        />
      </div>

      {/* Warnings Section */}
      {warnings.length > 0 && (
        <WarningsSection warnings={warnings} />
      )}
    </div>
  );
}

/**
 * MetricCard Sub-Component
 */
interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  count: number;
  message: string;
  confidence?: number;
}

function MetricCard({ icon, label, count, message, confidence }: MetricCardProps) {
  // Determine status icon based on confidence or count
  const statusIcon =
    confidence !== undefined && confidence >= 90 ? (
      <CheckCircle2 className="h-5 w-5 text-green-500" />
    ) : confidence !== undefined && confidence >= 70 ? (
      <AlertTriangle className="h-5 w-5 text-yellow-500" />
    ) : confidence !== undefined && confidence < 70 ? (
      <XCircle className="h-5 w-5 text-red-500" />
    ) : count > 0 ? (
      <CheckCircle2 className="h-5 w-5 text-green-500" />
    ) : null;

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="text-muted-foreground">{icon}</div>
            <span className="text-sm font-medium text-muted-foreground">{label}</span>
          </div>
          {statusIcon}
        </div>
        <div className="text-2xl font-bold mb-1">{count}</div>
        <div className="text-xs text-muted-foreground">{message}</div>
      </CardContent>
    </Card>
  );
}

/**
 * WarningsSection Sub-Component
 */
interface WarningsSectionProps {
  warnings: string[];
}

function WarningsSection({ warnings }: WarningsSectionProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Alert variant="default" className="cursor-pointer hover:bg-accent/50 transition-colors border-yellow-500/50">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          <AlertDescription className="flex items-center justify-between w-full">
            <span className="font-medium">
              {warnings.length} warning{warnings.length !== 1 ? 's' : ''} detected
            </span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            />
          </AlertDescription>
        </Alert>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 space-y-2">
        {warnings.map((warning, index) => (
          <Alert key={index} variant="default" className="border-yellow-500/30">
            <AlertDescription className="text-sm">{warning}</AlertDescription>
          </Alert>
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}
