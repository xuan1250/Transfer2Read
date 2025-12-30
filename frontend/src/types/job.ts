export type JobStatus = 'UPLOADED' | 'QUEUED' | 'ANALYZING' | 'EXTRACTING' | 'STRUCTURING' | 'GENERATING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface ElementMetrics {
  count: number;
  avg_confidence?: number;
  low_confidence_items?: Array<Record<string, unknown>>;
  detected_toc?: boolean; // For chapters
  pages?: number[]; // For multi_column_pages
  mapping?: Array<{ // For chapters - page-to-chapter mapping
    chapter_id: number;
    title: string;
    pdf_page_start: number;
    pdf_page_end: number;
  }>;
}

export interface FidelityTarget {
  target: number;
  actual: number;
  met: boolean;
}

export interface QualityReport {
  overall_confidence?: number; // 0-100
  elements?: {
    tables?: ElementMetrics;
    images?: ElementMetrics;
    equations?: ElementMetrics;
    chapters?: ElementMetrics;
    multi_column_pages?: ElementMetrics;
  };
  warnings?: string[];
  fidelity_targets?: Record<string, FidelityTarget>;
  estimated_cost?: number; // USD cost added in Story 5.1
  pages_processed?: number; // Total pages processed
}

export interface Job {
  id: string;
  user_id: string;
  status: JobStatus;
  input_path: string | null;
  original_filename?: string | null;
  output_path?: string | null;
  quality_report?: QualityReport;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  progress?: number; // 0-100
  stage_metadata?: Record<string, unknown>; // Current pipeline stage info
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
}

export interface DownloadUrlResponse {
  download_url: string;
  expires_at: string;
}

export type FeedbackRating = 'positive' | 'negative';

export interface FeedbackItem {
  id: string;
  rating: FeedbackRating;
  comment?: string | null;
  created_at: string;
}

export interface FeedbackListResponse {
  feedback: FeedbackItem[];
  total: number;
}

export type IssueType =
  | 'table_formatting'
  | 'missing_images'
  | 'broken_chapters'
  | 'incorrect_equations'
  | 'font_issues'
  | 'other';

export interface IssueItem {
  id: string;
  issue_type: IssueType;
  page_number?: number | null;
  description: string;
  screenshot_url?: string | null;
  created_at: string;
}

export interface IssueListResponse {
  issues: IssueItem[];
  total: number;
}
