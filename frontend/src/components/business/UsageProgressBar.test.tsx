/**
 * Unit tests for UsageProgressBar component
 */
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { UsageProgressBar } from '@/components/business/UsageProgressBar';
import { UsageStats } from '@/types/usage';

// Mock the useUser hook
vi.mock('@/hooks/useUser', () => ({
  useUser: vi.fn(),
}));

// Import after mocking
import { useUser } from '@/hooks/useUser';

// Mock fetch globally
global.fetch = vi.fn();

describe('UsageProgressBar', () => {
  const mockSession = {
    access_token: 'mock-token-123',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Loading State', () => {
    it('displays skeleton while loading', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<UsageProgressBar />);

      // Should show skeleton elements (check for animate-pulse class)
      const skeletonElements = container.querySelectorAll('.animate-pulse');
      expect(skeletonElements.length).toBeGreaterThan(0);
    });
  });

  describe('Error State', () => {
    it('handles error state gracefully when fetch fails', async () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('Unable to load usage data')).toBeInTheDocument();
      });
    });

    it('handles 401 unauthorized error', async () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('Unable to load usage data')).toBeInTheDocument();
      });
    });
  });

  describe('FREE Tier with Limits', () => {
    it('displays "X/Y Free Conversions Used This Month" format correctly', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 3,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 2,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument();
        expect(screen.getByText('/ 5')).toBeInTheDocument();
        expect(screen.getByText('Free Conversions Used This Month')).toBeInTheDocument();
      });
    });

    it('renders progress bar with correct percentage', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 3,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 2,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        // 3/5 = 60% - verify progress bar aria-label includes the percentage
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-label', '60% of monthly conversions used');
      });
    });

    it('shows remaining conversions text', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 3,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 2,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText(/conversions remaining/)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('shows singular "conversion" for 1 remaining', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 4,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 1,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText(/conversion remaining/)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('shows "No conversions remaining" when at limit', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 5,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 0,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('No conversions remaining')).toBeInTheDocument();
      });
    });
  });

  describe('Color Coding', () => {
    it('uses green for 0-60% usage', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 2,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 3,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        const countElement = screen.getByText('2');
        expect(countElement).toHaveClass('text-green-600');
      });
    });

    it('uses yellow/amber for 61-90% usage (warning state)', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 4,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 1,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        const countElement = screen.getByText('4');
        expect(countElement).toHaveClass('text-amber-600');
        expect(screen.getByText('Almost Full')).toBeInTheDocument();
      });
    });

    it('uses red for 91-100% usage (critical state)', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 5,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 0,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        const countElement = screen.getByText('5');
        expect(countElement).toHaveClass('text-red-600');
        expect(screen.getByText('Limit Reached')).toBeInTheDocument();
        expect(screen.getByText(/reached your monthly limit/)).toBeInTheDocument();
      });
    });
  });

  describe('PRO/PREMIUM Tiers', () => {
    it('displays "Unlimited" badge for PRO tier', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 15,
        tier: 'PRO',
        tier_limit: null,
        remaining: null,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'PRO' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('Unlimited')).toBeInTheDocument();
        expect(screen.getByText('15')).toBeInTheDocument();
        expect(screen.getByText('conversions this month')).toBeInTheDocument();
        expect(screen.getByText(/unlimited conversions with PRO tier/)).toBeInTheDocument();
      });
    });

    it('displays "Unlimited" badge for PREMIUM tier', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 25,
        tier: 'PREMIUM',
        tier_limit: null,
        remaining: null,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'PREMIUM' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(screen.getByText('Unlimited')).toBeInTheDocument();
        expect(screen.getByText('25')).toBeInTheDocument();
        expect(screen.getByText(/unlimited conversions with PREMIUM tier/)).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('fetches usage data from GET /api/v1/usage endpoint', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 3,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 2,
      };

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar />);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/usage'),
          expect.objectContaining({
            headers: {
              Authorization: 'Bearer mock-token-123',
            },
          })
        );
      });
    });

    it('calls onUsageLoaded callback when data is loaded', async () => {
      const mockUsage: UsageStats = {
        month: '2025-12',
        conversion_count: 3,
        tier: 'FREE',
        tier_limit: 5,
        remaining: 2,
      };

      const onUsageLoaded = vi.fn();

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
        session: mockSession,
      });

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsage,
      });

      render(<UsageProgressBar onUsageLoaded={onUsageLoaded} />);

      await waitFor(() => {
        expect(onUsageLoaded).toHaveBeenCalledWith(mockUsage);
      });
    });
  });
});
