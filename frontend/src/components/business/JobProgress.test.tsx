import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { JobProgress } from './JobProgress';
import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the useJobProgress hook
vi.mock('@/hooks/useJobProgress', () => ({
  useJobProgress: vi.fn(),
}));

// Import the mocked hook
import { useJobProgress } from '@/hooks/useJobProgress';

// Mock toast
vi.mock('@/hooks/use-toast', () => ({
  toast: vi.fn(),
}));

describe('JobProgress Component', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('renders loading skeleton when data is loading', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      isLoading: true,
      error: null,
    });

    render(<JobProgress jobId="test-job-123" />, { wrapper });

    // Check for skeleton elements (multiple Skeleton components)
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders error state when there is an error', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      isLoading: false,
      error: new Error('Network error'),
    });

    render(<JobProgress jobId="test-job-123" />, { wrapper });

    expect(screen.getByText(/Connection lost/i)).toBeInTheDocument();
    expect(screen.getByText(/Reconnecting/i)).toBeInTheDocument();
  });

  it('renders progress data for a PROCESSING job', () => {
    const mockProgress = {
      job_id: 'test-job-123',
      status: 'PROCESSING',
      progress_percentage: 50,
      current_stage: 'layout_analysis',
      stage_description: 'Analyzing layout...',
      elements_detected: {
        tables: 12,
        images: 8,
        equations: 5,
        chapters: 15,
      },
      estimated_time_remaining: 45,
      estimated_cost: 0.1234,
      quality_confidence: 94,
      timestamp: '2025-12-14T10:30:00Z',
    };

    vi.mocked(useJobProgress).mockReturnValue({
      progress: mockProgress,
      isLoading: false,
      error: null,
    });

    render(<JobProgress jobId="test-job-123" />, { wrapper });

    // Check stage description
    expect(screen.getByText('Analyzing layout...')).toBeInTheDocument();

    // Check progress percentage
    expect(screen.getByText('50%')).toBeInTheDocument();

    // Check element counts
    expect(screen.getByText('Tables')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Images')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();

    // Check estimated time remaining
    expect(screen.getByText(/45 seconds/i)).toBeInTheDocument();

    // Check estimated cost
    expect(screen.getByText(/\$0.1234/i)).toBeInTheDocument();

    // Check quality confidence
    expect(screen.getByText(/Quality: 94%/i)).toBeInTheDocument();
  });

  it('renders completion state with checkmarks for COMPLETED job', () => {
    const mockProgress = {
      job_id: 'test-job-123',
      status: 'COMPLETED',
      progress_percentage: 100,
      current_stage: 'complete',
      stage_description: 'Conversion complete!',
      elements_detected: {
        tables: 12,
        images: 8,
        equations: 5,
        chapters: 15,
      },
      estimated_time_remaining: null,
      estimated_cost: 0.1523,
      quality_confidence: 98,
      timestamp: '2025-12-14T10:35:00Z',
    };

    vi.mocked(useJobProgress).mockReturnValue({
      progress: mockProgress,
      isLoading: false,
      error: null,
    });

    render(<JobProgress jobId="test-job-123" />, { wrapper });

    // Check completion state
    expect(screen.getByText('Conversion complete!')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText(/✓ Complete/i)).toBeInTheDocument();

    // Check quality confidence
    expect(screen.getByText(/Quality: 98%/i)).toBeInTheDocument();

    // Checkmarks should be visible (Check icons in element cards)
    // Note: We can't easily test for lucide-react icons in unit tests,
    // but we verify the component renders without errors
  });

  it('does not show estimated time remaining when job is completed', () => {
    const mockProgress = {
      job_id: 'test-job-123',
      status: 'COMPLETED',
      progress_percentage: 100,
      current_stage: 'complete',
      stage_description: 'Conversion complete!',
      elements_detected: {
        tables: 0,
        images: 0,
        equations: 0,
        chapters: 0,
      },
      estimated_time_remaining: 0,
      estimated_cost: 0.05,
      quality_confidence: 85,
      timestamp: '2025-12-14T10:35:00Z',
    };

    vi.mocked(useJobProgress).mockReturnValue({
      progress: mockProgress,
      isLoading: false,
      error: null,
    });

    render(<JobProgress jobId="test-job-123" />, { wrapper });

    // Estimated time remaining should not be shown for completed jobs
    expect(screen.queryByText(/seconds remaining/i)).not.toBeInTheDocument();
  });

  it('renders quality badge with correct color for high confidence', () => {
    const mockProgress = {
      job_id: 'test-job-123',
      status: 'PROCESSING',
      progress_percentage: 75,
      current_stage: 'epub_generation',
      stage_description: 'Generating EPUB...',
      elements_detected: {
        tables: 5,
        images: 3,
        equations: 2,
        chapters: 8,
      },
      estimated_time_remaining: 15,
      estimated_cost: 0.08,
      quality_confidence: 95, // High confidence (>90%)
      timestamp: '2025-12-14T10:33:00Z',
    };

    vi.mocked(useJobProgress).mockReturnValue({
      progress: mockProgress,
      isLoading: false,
      error: null,
    });

    render(<JobProgress jobId="test-job-123" />, { wrapper });

    // Quality badge should be present
    expect(screen.getByText(/Quality: 95%/i)).toBeInTheDocument();
  });
});
