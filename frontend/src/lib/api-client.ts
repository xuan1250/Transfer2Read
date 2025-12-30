import { Job, JobListResponse, DownloadUrlResponse } from '@/types/job';
import { LimitExceededError } from '@/types/usage';
import { SystemStats, UserListParams, UserListResponse, TierUpdateRequest, TierUpdateResponse } from '@/types/admin';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Global handler for limit exceeded errors
// This will be set by the LimitModalProvider
let limitExceededHandler: ((error: LimitExceededError) => void) | null = null;

export function setLimitExceededHandler(handler: (error: LimitExceededError) => void) {
  limitExceededHandler = handler;
}

/**
 * Check if response is a limit exceeded error and handle it
 */
function handleLimitExceededError(response: Response, errorData: Record<string, unknown>): boolean {
  if (response.status === 403 && errorData.code) {
    const isLimitError =
      errorData.code === 'FILE_SIZE_LIMIT_EXCEEDED' ||
      errorData.code === 'CONVERSION_LIMIT_EXCEEDED';

    if (isLimitError && limitExceededHandler) {
      limitExceededHandler(errorData as unknown as LimitExceededError);
      return true;
    }
  }
  return false;
}

/**
 * Extract error message from API response
 */
function getErrorMessage(errorData: { detail?: unknown }, fallback: string): string {
  if (!errorData.detail) return fallback;

  // Handle nested detail object: {detail: {detail: "message", code: "CODE"}}
  if (typeof errorData.detail === 'object' && errorData.detail !== null && 'detail' in errorData.detail) {
    const nestedDetail = errorData.detail as { detail?: unknown };
    if (typeof nestedDetail.detail === 'string') {
      return nestedDetail.detail;
    }
  }

  // Handle simple string detail: {detail: "message"}
  if (typeof errorData.detail === 'string') {
    return errorData.detail;
  }

  return fallback;
}

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

    // Check for limit exceeded error and handle it
    if (handleLimitExceededError(response, errorData)) {
      throw new Error('LIMIT_EXCEEDED'); // Still throw to stop execution
    }

    throw new Error(getErrorMessage(errorData, 'Failed to fetch jobs'));
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

    // Check for limit exceeded error and handle it
    if (handleLimitExceededError(response, errorData)) {
      throw new Error('LIMIT_EXCEEDED');
    }

    throw new Error(getErrorMessage(errorData, 'Failed to fetch job'));
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

    // Check for limit exceeded error and handle it
    if (handleLimitExceededError(response, errorData)) {
      throw new Error('LIMIT_EXCEEDED');
    }

    throw new Error(getErrorMessage(errorData, 'Failed to get download URL'));
  }

  return response.json();
}

/**
 * Delete a job (hard delete)
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

    // Check for limit exceeded error and handle it
    if (handleLimitExceededError(response, errorData)) {
      throw new Error('LIMIT_EXCEEDED');
    }

    throw new Error(getErrorMessage(errorData, 'Failed to delete job'));
  }
}

/**
 * Admin API Functions
 */

/**
 * Get system statistics (admin only)
 */
export async function getAdminStats(token: string): Promise<SystemStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    if (response.status === 403) {
      throw new Error('FORBIDDEN');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(errorData, 'Failed to fetch system stats'));
  }

  return response.json();
}

/**
 * Get paginated user list with filters (admin only)
 */
export async function getAdminUsers(
  token: string,
  params: UserListParams = {}
): Promise<UserListResponse> {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.search) queryParams.append('search', params.search);
  if (params.tier_filter && params.tier_filter !== 'ALL') queryParams.append('tier_filter', params.tier_filter);
  if (params.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params.sort_order) queryParams.append('sort_order', params.sort_order);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/admin/users?${queryParams.toString()}`,
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
    if (response.status === 403) {
      throw new Error('FORBIDDEN');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(errorData, 'Failed to fetch users'));
  }

  return response.json();
}

/**
 * Update user tier (admin only)
 */
export async function updateUserTier(
  token: string,
  userId: string,
  tierData: TierUpdateRequest
): Promise<TierUpdateResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/admin/users/${userId}/tier`,
    {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tierData),
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    if (response.status === 403) {
      throw new Error('FORBIDDEN');
    }
    if (response.status === 404) {
      throw new Error('User not found');
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(errorData, 'Failed to update user tier'));
  }

  return response.json();
}
