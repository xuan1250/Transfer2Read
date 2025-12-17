/**
 * FeedbackWidget Component
 *
 * Displays thumbs up/down buttons for user feedback on conversion quality.
 * Story 5.4 - Download & Feedback Flow
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ThumbsUp, ThumbsDown, CheckCircle } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface FeedbackWidgetProps {
  jobId: string;
  onFeedbackSubmitted?: (rating: 'positive' | 'negative') => void;
}

export function FeedbackWidget({ jobId, onFeedbackSubmitted }: FeedbackWidgetProps) {
  const [submitted, setSubmitted] = useState(false);
  const [selectedRating, setSelectedRating] = useState<'positive' | 'negative' | null>(null);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCheckingExisting, setIsCheckingExisting] = useState(true);
  const supabase = createClient();
  const { toast } = useToast();

  // Check if feedback already exists on mount (AC #10 - duplicate prevention)
  React.useEffect(() => {
    const checkExistingFeedback = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}/feedback/check`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.has_feedback) {
            setSubmitted(true);
          }
        }
      } catch (err) {
        console.error('Error checking existing feedback:', err);
        // Don't block widget on error, just log it
      } finally {
        setIsCheckingExisting(false);
      }
    };

    checkExistingFeedback();
  }, [jobId, supabase]);

  const handleRatingClick = (rating: 'positive' | 'negative') => {
    setSelectedRating(rating);
  };

  const handleSubmit = async () => {
    if (!selectedRating) return;

    setIsSubmitting(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('Not authenticated');
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}/feedback`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rating: selectedRating,
          comment: comment.trim() || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || 'Failed to submit feedback');
      }

      setSubmitted(true);
      onFeedbackSubmitted?.(selectedRating);

      toast({
        title: 'Thank you for your feedback!',
        description: 'Your input helps us improve conversion quality.',
        variant: 'default',
      });
    } catch (err) {
      console.error('Feedback submission error:', err);
      toast({
        title: 'Failed to submit feedback',
        description: err instanceof Error ? err.message : 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Already submitted state
  if (submitted) {
    return (
      <div className="border rounded-lg p-6 bg-green-50 dark:bg-green-950/20">
        <div className="flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
          <p className="text-sm font-medium text-green-900 dark:text-green-100">
            Thank you for your feedback!
          </p>
        </div>
      </div>
    );
  }

  // Loading state while checking for existing feedback
  if (isCheckingExisting) {
    return (
      <div className="border rounded-lg p-6 space-y-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="flex gap-4">
          <div className="flex-1 h-12 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="flex-1 h-12 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-6 space-y-4">
      <h3 className="text-lg font-semibold">How was this conversion?</h3>

      {/* Rating Buttons */}
      <div className="flex gap-4">
        <Button
          variant={selectedRating === 'positive' ? 'default' : 'outline'}
          size="lg"
          onClick={() => handleRatingClick('positive')}
          disabled={isSubmitting}
          className="flex-1 gap-2"
        >
          <ThumbsUp className="h-5 w-5" />
          Good
        </Button>
        <Button
          variant={selectedRating === 'negative' ? 'default' : 'outline'}
          size="lg"
          onClick={() => handleRatingClick('negative')}
          disabled={isSubmitting}
          className="flex-1 gap-2"
        >
          <ThumbsDown className="h-5 w-5" />
          Needs Improvement
        </Button>
      </div>

      {/* Optional Comment (shown if negative selected) */}
      {selectedRating === 'negative' && (
        <div className="space-y-2">
          <label htmlFor="feedback-comment" className="text-sm font-medium">
            What went wrong? (optional)
          </label>
          <Textarea
            id="feedback-comment"
            placeholder="Tell us what could be improved..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            disabled={isSubmitting}
            rows={3}
            maxLength={2000}
          />
        </div>
      )}

      {/* Submit Button */}
      {selectedRating && (
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
        </Button>
      )}
    </div>
  );
}
