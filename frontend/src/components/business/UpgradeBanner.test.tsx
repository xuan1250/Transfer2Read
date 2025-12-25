/**
 * Unit tests for UpgradeBanner component
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { UpgradeBanner } from '@/components/business/UpgradeBanner';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock useUser hook
vi.mock('@/hooks/useUser', () => ({
  useUser: vi.fn(),
}));

// Import after mocking
import { useUser } from '@/hooks/useUser';

describe('UpgradeBanner', () => {
  const DISMISSAL_KEY = 'upgrade-banner-dismissed';

  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Conditional Rendering', () => {
    it('renders banner for FREE tier users', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      expect(screen.getByText('Unlock Unlimited Conversions with Pro')).toBeInTheDocument();
      expect(screen.getByText(/No limits on file size or monthly conversions/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /See Plans/i })).toBeInTheDocument();
    });

    it('does NOT render for PRO tier users', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'PRO' } },
      });

      const { container } = render(<UpgradeBanner />);

      expect(container).toBeEmptyDOMElement();
    });

    it('does NOT render for PREMIUM tier users', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'PREMIUM' } },
      });

      const { container } = render(<UpgradeBanner />);

      expect(container).toBeEmptyDOMElement();
    });

    it('defaults to FREE tier when user metadata is missing', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: {} },
      });

      render(<UpgradeBanner />);

      // Should render for default FREE tier
      expect(screen.getByText('Unlock Unlimited Conversions with Pro')).toBeInTheDocument();
    });
  });

  describe('Dismissal Functionality', () => {
    it('dismisses banner when close button is clicked', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      // Banner should be visible initially
      expect(screen.getByText('Unlock Unlimited Conversions with Pro')).toBeInTheDocument();

      // Click dismiss button
      const dismissButton = screen.getByRole('button', { name: /Dismiss banner/i });
      fireEvent.click(dismissButton);

      // Banner should be removed
      expect(screen.queryByText('Unlock Unlimited Conversions with Pro')).not.toBeInTheDocument();
    });

    it('persists dismissal state in localStorage', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      // Click dismiss button
      const dismissButton = screen.getByRole('button', { name: /Dismiss banner/i });
      fireEvent.click(dismissButton);

      // Check localStorage
      const dismissedAt = localStorage.getItem(DISMISSAL_KEY);
      expect(dismissedAt).not.toBeNull();
      expect(parseInt(dismissedAt!, 10)).toBeGreaterThan(Date.now() - 1000); // Within last second
    });

    it('does NOT render if dismissed within 7-day period', () => {
      // Set dismissal timestamp to 3 days ago
      const threeDaysAgo = Date.now() - (3 * 24 * 60 * 60 * 1000);
      localStorage.setItem(DISMISSAL_KEY, threeDaysAgo.toString());

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<UpgradeBanner />);

      // Banner should NOT render (still within 7-day dismissal)
      expect(container).toBeEmptyDOMElement();
    });

    it('renders again after 7-day dismissal period expires', () => {
      // Set dismissal timestamp to 8 days ago (expired)
      const eightDaysAgo = Date.now() - (8 * 24 * 60 * 60 * 1000);
      localStorage.setItem(DISMISSAL_KEY, eightDaysAgo.toString());

      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      // Banner should render again (dismissal expired)
      expect(screen.getByText('Unlock Unlimited Conversions with Pro')).toBeInTheDocument();

      // Old dismissal key should be removed
      const dismissedAt = localStorage.getItem(DISMISSAL_KEY);
      expect(dismissedAt).toBeNull();
    });
  });

  describe('CTA Button Navigation', () => {
    it('navigates to /pricing route when "See Plans" button is clicked', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      const ctaButton = screen.getByRole('button', { name: /See Plans/i });
      fireEvent.click(ctaButton);

      expect(mockPush).toHaveBeenCalledWith('/pricing');
      expect(mockPush).toHaveBeenCalledTimes(1);
    });
  });

  describe('Visual and Content Elements', () => {
    it('displays Sparkles icon', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<UpgradeBanner />);

      // Check for icon container with blue background
      const iconContainer = container.querySelector('.bg-blue-600');
      expect(iconContainer).toBeInTheDocument();
    });

    it('has correct headline and subtext', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      expect(screen.getByText('Unlock Unlimited Conversions with Pro')).toBeInTheDocument();
      expect(screen.getByText(/No limits on file size or monthly conversions/)).toBeInTheDocument();
      expect(screen.getByText(/priority support and faster processing/)).toBeInTheDocument();
    });

    it('has Professional Blue theme styling', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<UpgradeBanner />);

      // Check for gradient background (Professional Blue theme)
      const card = container.querySelector('.bg-gradient-to-r');
      expect(card).toHaveClass('from-blue-50', 'to-sky-50', 'border-blue-200');
    });

    it('CTA button has correct styling', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      const ctaButton = screen.getByRole('button', { name: /See Plans/i });
      expect(ctaButton).toHaveClass('bg-blue-600', 'hover:bg-blue-700', 'text-white');
    });
  });

  describe('Accessibility', () => {
    it('dismiss button has accessible label', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      const dismissButton = screen.getByRole('button', { name: /Dismiss banner/i });
      expect(dismissButton).toHaveAttribute('aria-label', 'Dismiss banner');
    });

    it('all interactive elements are keyboard accessible', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<UpgradeBanner />);

      // Both buttons should be focusable
      const dismissButton = screen.getByRole('button', { name: /Dismiss banner/i });
      const ctaButton = screen.getByRole('button', { name: /See Plans/i });

      expect(dismissButton.tagName).toBe('BUTTON');
      expect(ctaButton.tagName).toBe('BUTTON');
    });
  });
});
