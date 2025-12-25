/**
 * Unit tests for LimitReachedModal component
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LimitReachedModal } from '@/components/business/LimitReachedModal';
import { LimitExceededError } from '@/types/usage';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('LimitReachedModal', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const fileSizeLimitError: LimitExceededError = {
    detail: 'File size exceeds your tier limit. Maximum allowed: 50MB for Free tier.',
    code: 'FILE_SIZE_LIMIT_EXCEEDED',
    tier: 'FREE',
    upgrade_url: '/pricing',
    current_size_mb: 75.5,
    max_size_mb: 50,
  };

  const conversionLimitError: LimitExceededError = {
    detail: 'Monthly conversion limit reached. You have used 5/5 conversions this month.',
    code: 'CONVERSION_LIMIT_EXCEEDED',
    tier: 'FREE',
    upgrade_url: '/pricing',
    current_count: 5,
    limit: 5,
    reset_date: '2025-02-01',
  };

  it('renders modal when open with file size limit error', () => {
    render(
      <LimitReachedModal
        isOpen={true}
        onClose={mockOnClose}
        errorData={fileSizeLimitError}
      />
    );

    expect(screen.getByText('Limit Reached')).toBeInTheDocument();
    expect(screen.getByText(fileSizeLimitError.detail)).toBeInTheDocument();
    expect(screen.getByText('75.5 MB')).toBeInTheDocument();
    expect(screen.getByText(/50 MB allowed/)).toBeInTheDocument();
  });

  it('renders modal with conversion limit error', () => {
    render(
      <LimitReachedModal
        isOpen={true}
        onClose={mockOnClose}
        errorData={conversionLimitError}
      />
    );

    expect(screen.getByText('Limit Reached')).toBeInTheDocument();
    expect(screen.getByText(conversionLimitError.detail)).toBeInTheDocument();
    expect(screen.getByText('5 / 5')).toBeInTheDocument();
    expect(screen.getByText(/conversions used/)).toBeInTheDocument();
  });

  it('displays reset date when provided', () => {
    render(
      <LimitReachedModal
        isOpen={true}
        onClose={mockOnClose}
        errorData={conversionLimitError}
      />
    );

    expect(screen.getByText(/Resets on:/)).toBeInTheDocument();
    expect(screen.getByText(/February 1, 2025/)).toBeInTheDocument();
  });

  it('shows tier comparison with PRO and FREE features', () => {
    render(
      <LimitReachedModal
        isOpen={true}
        onClose={mockOnClose}
        errorData={fileSizeLimitError}
      />
    );

    // Use getAllByText for elements that appear multiple times
    expect(screen.getAllByText('PRO').length).toBeGreaterThan(0);
    expect(screen.getAllByText('FREE').length).toBeGreaterThan(0);
    expect(screen.getByText('Unlimited conversions')).toBeInTheDocument();
    expect(screen.getByText('Unlimited file size')).toBeInTheDocument();
  });

  it('calls onClose when "Maybe Later" button is clicked', () => {
    render(
      <LimitReachedModal
        isOpen={true}
        onClose={mockOnClose}
        errorData={fileSizeLimitError}
      />
    );

    const maybeLaterButton = screen.getByText('Maybe Later');
    fireEvent.click(maybeLaterButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('does not render when isOpen is false', () => {
    render(
      <LimitReachedModal
        isOpen={false}
        onClose={mockOnClose}
        errorData={fileSizeLimitError}
      />
    );

    expect(screen.queryByText('Limit Reached')).not.toBeInTheDocument();
  });

  it('is keyboard accessible (Esc key closes modal)', async () => {
    render(
      <LimitReachedModal
        isOpen={true}
        onClose={mockOnClose}
        errorData={fileSizeLimitError}
      />
    );

    // Simulate Escape key press
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });
});
