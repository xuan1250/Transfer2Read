import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useJobProgress } from './useJobProgress';
import type { ReactNode } from 'react';

// Mock Supabase client
const mockGetSession = vi.fn();
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}));

// Mock fetch globally
global.fetch = vi.fn();

describe('useJobProgress Hook', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false, // Disable retries for faster tests
        },
      },
    });

    // Default mock: user is authenticated
    mockGetSession.mockResolvedValue({
      data: {
        session: {
          access_token: 'mock-token-123',
        },
      },
    });
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  describe('Successful Progress Fetching', () => {
    it('fetches progress data for PROCESSING job', async () => {
      const mockProgressData = {
        job_id: 'test-job-123',
        status: 'PROCESSING',
        progress_percentage: 50,
        current_stage: 'layout_analysis',
        stage_description: 'Analyzing layout...',
        elements_detected: {
          tables: 12,
          images: 8,
          equations: 5,
          chapters: 0,
        },
        estimated_time_remaining: 45,
        estimated_cost: 0.12,
        quality_confidence: 94,
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData,
      });

      const { result } = renderHook(() => useJobProgress('test-job-123'), { wrapper });

      // Initially loading
      expect(result.current.isLoading).toBe(true);
      expect(result.current.progress).toBeUndefined();

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.progress).toBeDefined();
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.progress).toEqual(mockProgressData);

      // Verify fetch was called correctly
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/jobs/test-job-123/progress'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token-123',
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('fetches progress data for QUEUED job', async () => {
      const mockProgressData = {
        job_id: 'queued-job-456',
        status: 'QUEUED',
        progress_percentage: 0,
        current_stage: 'queued',
        stage_description: 'Waiting to start...',
        elements_detected: {
          tables: 0,
          images: 0,
          equations: 0,
          chapters: 0,
        },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData,
      });

      const { result } = renderHook(() => useJobProgress('queued-job-456'), { wrapper });

      await waitFor(() => {
        expect(result.current.progress).toBeDefined();
      });

      expect(result.current.progress?.status).toBe('QUEUED');
      expect(result.current.progress?.progress_percentage).toBe(0);
    });

    it('fetches progress data for COMPLETED job', async () => {
      const mockProgressData = {
        job_id: 'completed-job-789',
        status: 'COMPLETED',
        progress_percentage: 100,
        current_stage: 'completed',
        stage_description: 'Conversion complete!',
        elements_detected: {
          tables: 15,
          images: 10,
          equations: 8,
          chapters: 12,
        },
        estimated_cost: 0.25,
        quality_confidence: 98,
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData,
      });

      const { result } = renderHook(() => useJobProgress('completed-job-789'), { wrapper });

      await waitFor(() => {
        expect(result.current.progress).toBeDefined();
      });

      expect(result.current.progress?.status).toBe('COMPLETED');
      expect(result.current.progress?.progress_percentage).toBe(100);
      expect(result.current.progress?.quality_confidence).toBe(98);
    });
  });

  describe('Error Handling', () => {
    it('handles 404 not found error', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      const { result } = renderHook(() => useJobProgress('nonexistent-job'), { wrapper });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toBe('Job not found');
    });

    it('handles 403 unauthorized error', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 403,
      });

      const { result } = renderHook(() => useJobProgress('unauthorized-job'), { wrapper });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toBe('Unauthorized to access this job');
    });

    it('handles generic fetch failure', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const { result } = renderHook(() => useJobProgress('error-job'), { wrapper });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toBe('Failed to fetch progress');
    });

    it('handles authentication failure', async () => {
      mockGetSession.mockResolvedValueOnce({
        data: {
          session: null, // Not authenticated
        },
      });

      const { result } = renderHook(() => useJobProgress('test-job'), { wrapper });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toBe('Not authenticated');
    });

    it('handles network error', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error('Network connection failed')
      );

      const { result } = renderHook(() => useJobProgress('network-error-job'), { wrapper });

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toContain('Network connection failed');
    });
  });

  describe('Polling Behavior', () => {
    it('continues polling when job is PROCESSING', async () => {
      vi.useFakeTimers();

      const mockProgressData = {
        job_id: 'polling-job',
        status: 'PROCESSING',
        progress_percentage: 50,
        current_stage: 'layout_analysis',
        stage_description: 'Analyzing...',
        elements_detected: { tables: 0, images: 0, equations: 0, chapters: 0 },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => mockProgressData,
      });

      renderHook(() => useJobProgress('polling-job'), { wrapper });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 2 seconds (polling interval)
      vi.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });

      vi.useRealTimers();
    });

    it('stops polling when job is COMPLETED', async () => {
      vi.useFakeTimers();

      const mockProgressData = {
        job_id: 'completed-polling-job',
        status: 'COMPLETED',
        progress_percentage: 100,
        current_stage: 'completed',
        stage_description: 'Done!',
        elements_detected: { tables: 15, images: 10, equations: 8, chapters: 12 },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => mockProgressData,
      });

      renderHook(() => useJobProgress('completed-polling-job'), { wrapper });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 5 seconds - should NOT poll again
      vi.advanceTimersByTime(5000);

      // Should still be only 1 call (no polling for COMPLETED status)
      expect(global.fetch).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });

    it('stops polling when job is FAILED', async () => {
      vi.useFakeTimers();

      const mockProgressData = {
        job_id: 'failed-polling-job',
        status: 'FAILED',
        progress_percentage: 50,
        current_stage: 'failed',
        stage_description: 'Conversion failed',
        elements_detected: { tables: 0, images: 0, equations: 0, chapters: 0 },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => mockProgressData,
      });

      renderHook(() => useJobProgress('failed-polling-job'), { wrapper });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });

      // Fast-forward 5 seconds - should NOT poll again
      vi.advanceTimersByTime(5000);

      // Should still be only 1 call (no polling for FAILED status)
      expect(global.fetch).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });
  });

  describe('Refetch Functionality', () => {
    it('allows manual refetch via refetch function', async () => {
      const mockProgressData = {
        job_id: 'refetch-job',
        status: 'PROCESSING',
        progress_percentage: 25,
        current_stage: 'layout_analysis',
        stage_description: 'Analyzing...',
        elements_detected: { tables: 5, images: 3, equations: 0, chapters: 0 },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
        ok: true,
        json: async () => mockProgressData,
      });

      const { result } = renderHook(() => useJobProgress('refetch-job'), { wrapper });

      await waitFor(() => {
        expect(result.current.progress).toBeDefined();
      });

      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Manually trigger refetch
      await result.current.refetch();

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('API URL Configuration', () => {
    it('uses NEXT_PUBLIC_API_URL if provided', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL;
      process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com';

      const mockProgressData = {
        job_id: 'test-job',
        status: 'QUEUED',
        progress_percentage: 0,
        current_stage: 'queued',
        stage_description: 'Waiting...',
        elements_detected: { tables: 0, images: 0, equations: 0, chapters: 0 },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData,
      });

      renderHook(() => useJobProgress('test-job'), { wrapper });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'https://api.example.com/api/v1/jobs/test-job/progress',
          expect.any(Object)
        );
      });

      // Restore original env
      process.env.NEXT_PUBLIC_API_URL = originalEnv;
    });

    it('falls back to localhost if NEXT_PUBLIC_API_URL not set', async () => {
      const originalEnv = process.env.NEXT_PUBLIC_API_URL;
      delete process.env.NEXT_PUBLIC_API_URL;

      const mockProgressData = {
        job_id: 'test-job',
        status: 'QUEUED',
        progress_percentage: 0,
        current_stage: 'queued',
        stage_description: 'Waiting...',
        elements_detected: { tables: 0, images: 0, equations: 0, chapters: 0 },
        timestamp: new Date().toISOString(),
      };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData,
      });

      renderHook(() => useJobProgress('test-job'), { wrapper });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/jobs/test-job/progress',
          expect.any(Object)
        );
      });

      // Restore original env
      process.env.NEXT_PUBLIC_API_URL = originalEnv;
    });
  });
});
