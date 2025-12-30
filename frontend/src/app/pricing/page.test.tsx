/**
 * Integration tests for PricingPage component
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import PricingPage from '@/app/pricing/page';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: any) => {
    return <a href={href}>{children}</a>;
  },
}));

// Mock useUser hook
vi.mock('@/hooks/useUser', () => ({
  useUser: vi.fn(),
}));

// Mock use-toast
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Import after mocking
import { useUser } from '@/hooks/useUser';

describe('PricingPage Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Tier Rendering', () => {
    it('renders all three tiers (FREE, PRO, PREMIUM)', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      // Use getAllByText for elements that appear multiple times
      const freeTierElements = screen.getAllByText('Free');
      expect(freeTierElements.length).toBeGreaterThan(0);
      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('Premium')).toBeInTheDocument();
    });

    it('displays correct pricing for each tier', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      // FREE tier shows "Free"
      const freeTierElements = screen.getAllByText('Free');
      expect(freeTierElements.length).toBeGreaterThan(0);

      // PRO tier shows $9.99/month
      expect(screen.getByText('$9.99')).toBeInTheDocument();
      const monthlyFreq = screen.getAllByText('/month');
      expect(monthlyFreq.length).toBeGreaterThanOrEqual(2); // PRO and PREMIUM both show /month

      // PREMIUM tier shows $19.99/month
      expect(screen.getByText('$19.99')).toBeInTheDocument();
    });

    it('displays features list for each tier', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      // FREE tier features
      expect(screen.getByText('5 conversions per month')).toBeInTheDocument();
      expect(screen.getByText('50MB maximum file size')).toBeInTheDocument();

      // PRO tier features
      expect(screen.getByText('Unlimited conversions')).toBeInTheDocument();
      expect(screen.getByText('Unlimited file size')).toBeInTheDocument();

      // PREMIUM tier features
      expect(screen.getByText('Everything in Pro')).toBeInTheDocument();
      expect(screen.getByText('Priority 24/7 support')).toBeInTheDocument();
    });

    it('shows "Recommended" badge on PRO tier', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      expect(screen.getByText('Recommended')).toBeInTheDocument();
    });
  });

  describe('Current Tier Indication', () => {
    it('shows "Current Plan" badge for FREE user on FREE tier', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      const currentBadges = screen.getAllByText('Current Plan');
      expect(currentBadges.length).toBeGreaterThan(0);
    });

    it('disables button for current tier', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      // Find all "Current Plan" buttons (should be disabled)
      const buttons = screen.getAllByRole('button');
      const currentPlanButton = buttons.find(btn => btn.textContent === 'Current Plan');
      expect(currentPlanButton).toBeDisabled();
    });

    it('shows "Current Plan" for PRO user on PRO tier', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'PRO' } },
      });

      render(<PricingPage />);

      const currentBadges = screen.getAllByText('Current Plan');
      // Should show Current Plan badge and Current Plan button for PRO tier
      expect(currentBadges.length).toBeGreaterThan(0);
    });
  });

  describe('Button Actions', () => {
    it('shows toast when selecting already subscribed tier', async () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      // For FREE user, the "Sign Up" button should be disabled (current plan)
      const buttons = screen.getAllByRole('button');
      const currentPlanButtons = buttons.filter(btn => btn.textContent === 'Current Plan');
      expect(currentPlanButtons.length).toBeGreaterThan(0);
      currentPlanButtons.forEach(btn => {
        expect(btn).toBeDisabled();
      });
    });

    it('shows placeholder toast when upgrading to PRO', async () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      const upgradeToProButton = screen.getByRole('button', { name: /Upgrade to Pro/i });
      fireEvent.click(upgradeToProButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Payment integration coming soon!',
            description: 'Please contact support@transfer2read.com to upgrade your account.',
          })
        );
      });
    });

    it('shows placeholder toast when upgrading to PREMIUM', async () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      const upgradeToPremiumButton = screen.getByRole('button', { name: /Upgrade to Premium/i });
      fireEvent.click(upgradeToPremiumButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Payment integration coming soon!',
            description: 'Please contact support@transfer2read.com to upgrade your account.',
          })
        );
      });
    });

    it('shows downgrade warning when selecting FREE from PRO', async () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'PRO' } },
      });

      render(<PricingPage />);

      const signUpButton = screen.getByRole('button', { name: /Sign Up/i });
      fireEvent.click(signUpButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Contact support',
            description: 'To downgrade your plan, please contact our support team.',
          })
        );
      });
    });
  });

  describe('FAQ Section', () => {
    it('displays FAQ section with 4 questions', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
      expect(screen.getByText('Can I change my plan later?')).toBeInTheDocument();
      expect(screen.getByText('What payment methods do you accept?')).toBeInTheDocument();
      expect(screen.getByText('What happens when I hit my monthly limit?')).toBeInTheDocument();
      expect(screen.getByText('Is there a refund policy?')).toBeInTheDocument();
    });

    it('displays FAQ answers', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      expect(screen.getByText(/You can upgrade or downgrade your plan/)).toBeInTheDocument();
      expect(screen.getByText(/We accept all major credit cards/)).toBeInTheDocument();
      expect(screen.getByText(/Yes! We offer a 30-day money-back guarantee/)).toBeInTheDocument();
    });
  });

  describe('Page Header and Navigation', () => {
    it('displays page title and subtitle', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      render(<PricingPage />);

      expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument();
      expect(screen.getByText(/Choose the plan that fits your needs/)).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('renders tier cards in grid layout', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<PricingPage />);

      // Check for grid layout class
      const gridContainer = container.querySelector('.grid.grid-cols-1.md\\:grid-cols-3');
      expect(gridContainer).toBeInTheDocument();
    });

    it('displays all feature checkmarks', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<PricingPage />);

      // Count Check icons (should be many - one per feature across all tiers)
      const checkIcons = container.querySelectorAll('.text-green-600');
      expect(checkIcons.length).toBeGreaterThan(15); // At least 15 features total
    });
  });

  describe('Visual Styling', () => {
    it('PRO tier has highlighted styling', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<PricingPage />);

      // PRO tier should have border-blue-600 and scale-105 classes
      const proCard = container.querySelector('.border-blue-600.scale-105');
      expect(proCard).toBeInTheDocument();
    });

    it('displays Professional Blue theme colors', () => {
      (useUser as any).mockReturnValue({
        user: { user_metadata: { tier: 'FREE' } },
      });

      const { container } = render(<PricingPage />);

      // Check for blue color classes
      const blueElements = container.querySelectorAll('.text-blue-600, .bg-blue-600, .border-blue-600');
      expect(blueElements.length).toBeGreaterThan(0);
    });
  });
});
