/**
 * Admin Dashboard Types
 *
 * TypeScript interfaces for admin dashboard data structures.
 */

export interface SystemStats {
  total_users: number;
  total_conversions: number;
  active_jobs: number;
  monthly_conversions: number;
}

export interface AdminUser {
  id: string;
  email: string;
  tier: 'FREE' | 'PRO' | 'PREMIUM';
  total_conversions: number;
  last_login: string | null;
  created_at: string;
}

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  tier_filter?: 'ALL' | 'FREE' | 'PRO' | 'PREMIUM';
  sort_by?: 'email' | 'tier' | 'conversions' | 'last_login' | 'created_at';
  sort_order?: 'asc' | 'desc';
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TierUpdateRequest {
  tier: 'FREE' | 'PRO' | 'PREMIUM';
}

export interface TierUpdateResponse {
  user_id: string;
  old_tier: string;
  new_tier: string;
  updated_at: string;
}
