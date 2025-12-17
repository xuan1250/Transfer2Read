/**
 * Confetti Animation Utilities
 *
 * Wrapper for canvas-confetti with accessibility support.
 * Story 5.4 - Download & Feedback Flow
 */

import confetti from 'canvas-confetti';

/**
 * Triggers a celebratory confetti animation for successful downloads.
 * Respects user's motion sensitivity preferences (prefers-reduced-motion).
 *
 * @param options - Optional confetti customization options
 */
export function triggerDownloadConfetti(options?: confetti.Options) {
  // Check user's motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReducedMotion) {
    // Skip animation for users with motion sensitivity
    return;
  }

  // Professional Blue theme colors (#2563eb, #0ea5e9, #10b981)
  const colors = ['#2563eb', '#0ea5e9', '#10b981', '#3b82f6', '#14b8a6'];

  // Trigger confetti burst
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 },
    colors,
    ...options,
  });
}

/**
 * Checks if confetti has already been shown for a specific job.
 * Uses localStorage to prevent duplicate animations on page refresh.
 *
 * @param jobId - The job ID to check
 * @returns true if confetti has already been shown
 */
export function hasShownConfetti(jobId: string): boolean {
  try {
    const key = `confetti-shown-${jobId}`;
    return localStorage.getItem(key) === 'true';
  } catch {
    // localStorage might be disabled
    return false;
  }
}

/**
 * Marks confetti as shown for a specific job.
 *
 * @param jobId - The job ID to mark
 */
export function markConfettiShown(jobId: string): void {
  try {
    const key = `confetti-shown-${jobId}`;
    localStorage.setItem(key, 'true');
  } catch {
    // localStorage might be disabled, fail silently
  }
}

/**
 * Triggers confetti only if it hasn't been shown before for this job.
 *
 * @param jobId - The job ID
 * @param options - Optional confetti customization options
 */
export function triggerConfettiOnce(jobId: string, options?: confetti.Options): void {
  if (!hasShownConfetti(jobId)) {
    triggerDownloadConfetti(options);
    markConfettiShown(jobId);
  }
}
