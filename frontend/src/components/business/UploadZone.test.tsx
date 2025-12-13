import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import UploadZone from './UploadZone';

// Mock axios
vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

// Mock Supabase client
const mockGetSession = vi.fn();
vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}));

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe('UploadZone Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock: user is logged in as FREE tier
    mockGetSession.mockResolvedValue({
      data: {
        session: {
          access_token: 'mock-token',
          user: {
            user_metadata: {
              tier: 'FREE',
            },
          },
        },
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders upload zone with correct default state', () => {
      render(<UploadZone />);

      expect(screen.getByRole('button', { name: /upload pdf file/i })).toBeInTheDocument();
      expect(screen.getByText(/drag and drop your pdf here/i)).toBeInTheDocument();
      expect(screen.getByText(/or click to browse/i)).toBeInTheDocument();
      expect(screen.getByText(/max 50mb/i)).toBeInTheDocument();
    });

    it('displays unlimited file size for PRO tier', async () => {
      mockGetSession.mockResolvedValue({
        data: {
          session: {
            access_token: 'mock-token',
            user: {
              user_metadata: {
                tier: 'PRO',
              },
            },
          },
        },
      });

      render(<UploadZone />);

      await waitFor(() => {
        expect(screen.getByText(/unlimited file size/i)).toBeInTheDocument();
      });
    });
  });

  describe('Drag-and-Drop Functionality', () => {
    it('highlights upload zone on drag enter', () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      fireEvent.dragEnter(zone);

      expect(zone).toHaveClass('border-blue-600');
      expect(zone).toHaveClass('bg-blue-50');
    });

    it('returns to default state on drag leave', () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      fireEvent.dragEnter(zone);
      fireEvent.dragLeave(zone, { currentTarget: zone, target: zone });

      expect(zone).not.toHaveClass('border-blue-600');
    });

    it('uploads file on drop', async () => {
      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = {
        files: [file],
      };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/upload'),
          expect.any(FormData),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer mock-token',
            }),
          })
        );
      });
    });

    it('shows error when multiple files are dropped', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file1 = new File(['dummy content 1'], 'test1.pdf', { type: 'application/pdf' });
      const file2 = new File(['dummy content 2'], 'test2.pdf', { type: 'application/pdf' });
      const dataTransfer = {
        files: [file1, file2],
      };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/only one file can be uploaded at a time/i)).toBeInTheDocument();
      });
    });
  });

  describe('Click-to-Browse Functionality', () => {
    it('opens file dialog on click', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file.*drag and drop/i });

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const clickSpy = vi.spyOn(fileInput, 'click');

      fireEvent.click(zone);

      expect(clickSpy).toHaveBeenCalled();
    });

    it('opens file dialog on Enter key', () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file.*drag and drop/i });

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const clickSpy = vi.spyOn(fileInput, 'click');

      fireEvent.keyDown(zone, { key: 'Enter' });

      expect(clickSpy).toHaveBeenCalled();
    });

    it('opens file dialog on Space key', () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file.*drag and drop/i });

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const clickSpy = vi.spyOn(fileInput, 'click');

      fireEvent.keyDown(zone, { key: ' ' });

      expect(clickSpy).toHaveBeenCalled();
    });

    it('uploads file on input change', async () => {
      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone />);
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalled();
      });
    });
  });

  describe('File Validation', () => {
    it('rejects non-PDF files', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'image.jpg', { type: 'image/jpeg' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/please upload a pdf file/i)).toBeInTheDocument();
      });
    });

    it('rejects oversized files for FREE tier', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      // Create a 60MB file (exceeds FREE tier limit of 50MB)
      const largeContent = new Array(60 * 1024 * 1024).fill('a').join('');
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });

      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/file size exceeds your tier limit/i)).toBeInTheDocument();
      });
    });

    it('accepts large files for PRO tier', async () => {
      mockGetSession.mockResolvedValue({
        data: {
          session: {
            access_token: 'mock-token',
            user: {
              user_metadata: {
                tier: 'PRO',
              },
            },
          },
        },
      });

      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone />);

      // Wait for tier to be loaded
      await waitFor(() => {
        expect(screen.getByText(/unlimited file size/i)).toBeInTheDocument();
      });

      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      // Create a 60MB file (should be accepted for PRO tier)
      const largeContent = new Array(60 * 1024 * 1024).fill('a').join('');
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });

      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalled();
      });
    });

    it('rejects empty files', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File([], 'empty.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/file is empty or corrupted/i)).toBeInTheDocument();
      });
    });
  });

  describe('Upload Progress', () => {
    it('displays progress bar during upload', async () => {
      let progressCallback: ((progressEvent: { loaded: number; total: number }) => void) | undefined;

      mockedAxios.post = vi.fn().mockImplementation((url, data, config) => {
        progressCallback = config?.onUploadProgress;
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve({ data: { job_id: 'test-job-123' } });
          }, 100);
        });
      });

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      // Wait for upload to start
      await waitFor(() => {
        expect(screen.getByText(/uploading/i)).toBeInTheDocument();
      });

      // Simulate progress update
      if (progressCallback) {
        progressCallback({ loaded: 50, total: 100 });
      }

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });
    });

    it('shows success message after upload completes', async () => {
      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays network error message', async () => {
      mockedAxios.post = vi.fn().mockRejectedValue(new Error('Network error'));

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/upload failed/i)).toBeInTheDocument();
      });
    });

    it('redirects to login on 401 error', async () => {
      interface AxiosLikeError extends Error {
        isAxiosError: boolean;
        response: { status: number };
      }

      const axiosError = new Error('Unauthorized') as AxiosLikeError;
      axiosError.isAxiosError = true;
      axiosError.response = { status: 401 };

      mockedAxios.post = vi.fn().mockRejectedValue(axiosError);
      mockedAxios.isAxiosError = vi.fn().mockReturnValue(true);

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file.*drag and drop/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('/login'));
      }, { timeout: 3000 });
    });

    it('displays file size error on 413 error', async () => {
      interface AxiosLikeError extends Error {
        isAxiosError: boolean;
        response: { status: number };
      }

      const axiosError = new Error('Payload Too Large') as AxiosLikeError;
      axiosError.isAxiosError = true;
      axiosError.response = { status: 413 };

      mockedAxios.post = vi.fn().mockRejectedValue(axiosError);
      mockedAxios.isAxiosError = vi.fn().mockReturnValue(true);

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file.*drag and drop/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/file exceeds tier limit/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('displays server error on 500 error', async () => {
      interface AxiosLikeError extends Error {
        isAxiosError: boolean;
        response: { status: number };
      }

      const axiosError = new Error('Server Error') as AxiosLikeError;
      axiosError.isAxiosError = true;
      axiosError.response = { status: 500 };

      mockedAxios.post = vi.fn().mockRejectedValue(axiosError);
      mockedAxios.isAxiosError = vi.fn().mockReturnValue(true);

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file.*drag and drop/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('allows manual error dismissal', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'image.jpg', { type: 'image/jpeg' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/please upload a pdf file/i)).toBeInTheDocument();
      });

      const dismissButton = screen.getByLabelText(/dismiss error/i);
      fireEvent.click(dismissButton);

      await waitFor(() => {
        expect(screen.queryByText(/please upload a pdf file/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Success Flow', () => {
    it('redirects to job page after successful upload', async () => {
      vi.useFakeTimers();

      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
      });

      // Fast-forward 1 second for auto-redirect
      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/jobs/test-job-123');
      });

      vi.useRealTimers();
    });

    it('calls onUploadSuccess callback', async () => {
      const onSuccess = vi.fn();

      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone onUploadSuccess={onSuccess} />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith('test-job-123');
      });
    });

    it('allows immediate navigation via View Job button', async () => {
      mockedAxios.post = vi.fn().mockResolvedValue({
        data: { job_id: 'test-job-123' },
      });

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
      });

      const viewJobButton = screen.getByRole('button', { name: /view job now/i });
      fireEvent.click(viewJobButton);

      expect(mockPush).toHaveBeenCalledWith('/jobs/test-job-123');
    });
  });

  describe('Accessibility', () => {
    it('has correct ARIA attributes', () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      expect(zone).toHaveAttribute('aria-label');
      expect(zone).toHaveAttribute('tabindex', '0');
    });

    it('announces errors to screen readers', async () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'image.jpg', { type: 'image/jpeg' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('is keyboard navigable', () => {
      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      zone.focus();
      expect(zone).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    it('prevents interaction during upload', async () => {
      let resolveUpload: ((value: { data: { job_id: string } }) => void) | undefined;
      const uploadPromise = new Promise<{ data: { job_id: string } }>((resolve) => {
        resolveUpload = resolve;
      });

      mockedAxios.post = vi.fn().mockReturnValue(uploadPromise);

      render(<UploadZone />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      const file = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/uploading/i)).toBeInTheDocument();
      });

      // Try to interact during upload
      expect(zone).toHaveClass('pointer-events-none');

      // Resolve upload
      resolveUpload!({ data: { job_id: 'test-job-123' } });
    });

    it('handles custom maxSizeMB prop', async () => {
      render(<UploadZone maxSizeMB={10} />);
      const zone = screen.getByRole('button', { name: /upload pdf file/i });

      // Create an 11MB file (exceeds custom limit)
      const largeContent = new Array(11 * 1024 * 1024).fill('a').join('');
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });

      const dataTransfer = { files: [file] };

      fireEvent.drop(zone, { dataTransfer });

      await waitFor(() => {
        expect(screen.getByText(/file size exceeds your tier limit/i)).toBeInTheDocument();
      });
    });
  });
});
