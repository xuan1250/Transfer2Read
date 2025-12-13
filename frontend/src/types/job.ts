export type JobStatus = 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

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
  input_path: string;
  output_path?: string;
  quality_report?: QualityReport;
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
