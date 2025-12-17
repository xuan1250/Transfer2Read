/**
 * IssueReportModal Component
 *
 * Modal dialog for reporting conversion issues with detailed information.
 * Story 5.4 - Download & Feedback Flow
 */

'use client';

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { createClient } from '@/lib/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface IssueReportModalProps {
  jobId: string;
  isOpen: boolean;
  onClose: () => void;
  onIssueSubmitted?: () => void;
}

type IssueType = 'table_formatting' | 'missing_images' | 'broken_chapters' | 'incorrect_equations' | 'font_issues' | 'other';

const ISSUE_TYPES: { value: IssueType; label: string }[] = [
  { value: 'table_formatting', label: 'Table Formatting' },
  { value: 'missing_images', label: 'Missing Images' },
  { value: 'broken_chapters', label: 'Broken Chapters' },
  { value: 'incorrect_equations', label: 'Incorrect Equations' },
  { value: 'font_issues', label: 'Font Issues' },
  { value: 'other', label: 'Other' },
];

export function IssueReportModal({ jobId, isOpen, onClose, onIssueSubmitted }: IssueReportModalProps) {
  const [issueType, setIssueType] = useState<IssueType>('table_formatting');
  const [pageNumber, setPageNumber] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const supabase = createClient();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate description
    if (description.trim().length < 10) {
      toast({
        title: 'Description too short',
        description: 'Please provide at least 10 characters describing the issue.',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('Not authenticated');
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}/issues`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          issue_type: issueType,
          page_number: pageNumber ? parseInt(pageNumber, 10) : null,
          description: description.trim(),
          screenshot_url: null, // Future enhancement
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.detail || 'Failed to submit issue report');
      }

      toast({
        title: 'Issue reported successfully',
        description: 'Thank you for helping us improve!',
        variant: 'default',
      });

      onIssueSubmitted?.();
      handleClose();
    } catch (err) {
      console.error('Issue report error:', err);
      toast({
        title: 'Failed to submit issue report',
        description: err instanceof Error ? err.message : 'Please try again later',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form
    setIssueType('table_formatting');
    setPageNumber('');
    setDescription('');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Report an Issue</DialogTitle>
          <DialogDescription>
            Help us improve by reporting problems with the conversion output.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Issue Type */}
          <div className="space-y-2">
            <Label htmlFor="issue-type">Issue Type *</Label>
            <Select value={issueType} onValueChange={(value) => setIssueType(value as IssueType)}>
              <SelectTrigger id="issue-type">
                <SelectValue placeholder="Select issue type" />
              </SelectTrigger>
              <SelectContent>
                {ISSUE_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Page Number */}
          <div className="space-y-2">
            <Label htmlFor="page-number">Page Number (Optional)</Label>
            <Input
              id="page-number"
              type="number"
              min="1"
              placeholder="e.g., 42"
              value={pageNumber}
              onChange={(e) => setPageNumber(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              placeholder="Describe the issue in detail (minimum 10 characters)..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isSubmitting}
              rows={4}
              maxLength={5000}
              required
            />
            <p className="text-xs text-muted-foreground">
              {description.length}/5000 characters
            </p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Submit Report'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
