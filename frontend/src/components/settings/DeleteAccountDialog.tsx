'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

interface DeleteAccountDialogProps {
  userEmail: string;
}

export function DeleteAccountDialog({ userEmail }: DeleteAccountDialogProps) {
  const [confirmEmail, setConfirmEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  const handleDeleteAccount = async () => {
    try {
      setLoading(true);
      setError(null);

      // Verify email confirmation
      if (confirmEmail !== userEmail) {
        setError('Email does not match. Please enter your exact email address.');
        setLoading(false);
        return;
      }

      // Get current session to extract JWT token
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) {
        setError('Authentication required. Please sign in again.');
        setLoading(false);
        return;
      }

      // Call backend API to delete account (server-side with admin privileges)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/users/me`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete account' }));
        setError(errorData.detail || 'Failed to delete account. Please try again.');
        setLoading(false);
        return;
      }

      // Account deleted successfully - sign out user
      await supabase.auth.signOut();

      // Redirect to homepage with success message
      router.push('/?message=Your account has been deleted successfully');
    } catch (err) {
      console.error('Delete account error:', err);
      setError('An unexpected error occurred. Please try again or contact support.');
      setLoading(false);
    }
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive" className="bg-red-600 hover:bg-red-700 text-white">
          Delete Account
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-red-600 flex items-center gap-2">
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            Delete Account
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-4 pt-2">
            <p className="text-gray-700 font-medium">
              This action cannot be undone. This will permanently delete your account and remove all your data from our servers.
            </p>

            {/* Error Alert */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            {/* Email Confirmation */}
            <div className="space-y-2">
              <Label htmlFor="confirm-email" className="text-gray-700">
                Type your email to confirm: <span className="font-semibold">{userEmail}</span>
              </Label>
              <Input
                id="confirm-email"
                type="email"
                placeholder={userEmail}
                value={confirmEmail}
                onChange={(e) => {
                  setConfirmEmail(e.target.value);
                  setError(null);
                }}
                className="focus:ring-red-500 border-gray-300"
              />
            </div>

            <p className="text-sm text-gray-600">
              The following data will be deleted:
            </p>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              <li>Your account and profile information</li>
              <li>All conversion jobs and history</li>
              <li>All uploaded PDFs and generated EPUBs</li>
            </ul>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => { setConfirmEmail(''); setError(null); }}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteAccount}
            disabled={loading || confirmEmail !== userEmail}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {loading ? 'Deleting Account...' : 'Delete My Account'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
