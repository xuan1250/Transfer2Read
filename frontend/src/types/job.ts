export type JobStatus = 'UPLOADED' | 'QUEUED' | 'ANALYZING' | 'EXTRACTING' | 'STRUCTURING' | 'GENERATING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface QualityReport {
  overall_confidence?: number;
  tables?: {
    count: number;
    avg_confidence?: number;
  };
  images?: {
    count: number;
  };
  equations?: {
    count: number;
    avg_confidence?: number;
  };
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
