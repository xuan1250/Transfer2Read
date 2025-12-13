import { Job, JobListResponse, DownloadUrlResponse } from '@/types/job';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch list of jobs with pagination
 */
export async function fetchJobs(
  token: string,
  limit: number = 20,
  offset: number = 0
): Promise<JobListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/jobs?limit=${limit}&offset=${offset}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch jobs');
  }

  return response.json();
}

/**
 * Fetch a single job by ID
 */
export async function fetchJob(token: string, jobId: string): Promise<Job> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/jobs/${jobId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch job');
  }

  return response.json();
}

/**
 * Get download URL for a completed job
 */
export async function getDownloadUrl(
  token: string,
  jobId: string
): Promise<DownloadUrlResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/jobs/${jobId}/download`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    if (response.status === 404) {
      throw new Error('File not found or job not completed');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to get download URL');
  }

  return response.json();
}

/**
 * Delete a job (soft delete)
 */
export async function deleteJob(token: string, jobId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/jobs/${jobId}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    if (response.status === 404) {
      // Job already deleted or doesn't exist - treat as success
      return;
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete job');
  }
}
