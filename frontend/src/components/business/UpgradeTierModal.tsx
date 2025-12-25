/**
 * UpgradeTierModal Component
 *
 * Modal dialog for upgrading a user's subscription tier.
 * Shows current tier, new tier selection, and confirmation.
 */
'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AdminUser } from '@/types/admin';
import { AlertCircle } from 'lucide-react';

interface UpgradeTierModalProps {
  user: AdminUser | null;
  open: boolean;
  onClose: () => void;
  onConfirm: (userId: string, newTier: 'FREE' | 'PRO' | 'PREMIUM') => Promise<void>;
}

export default function UpgradeTierModal({
  user,
  open,
  onClose,
  onConfirm,
}: UpgradeTierModalProps) {
  const [selectedTier, setSelectedTier] = useState<'FREE' | 'PRO' | 'PREMIUM' | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleClose = () => {
    setSelectedTier(null);
    setShowConfirm(false);
    onClose();
  };

  const handleSubmit = async () => {
    if (!user || !selectedTier) return;

    setLoading(true);
    try {
      await onConfirm(user.id, selectedTier);
      handleClose();
    } catch (error) {
      // Error handling is done by parent component (toast)
    } finally {
      setLoading(false);
    }
  };

  const getTierBadgeColor = (tier: string) => {
    switch (tier) {
      case 'FREE':
        return 'bg-gray-100 text-gray-700';
      case 'PRO':
        return 'bg-blue-100 text-blue-700';
      case 'PREMIUM':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Upgrade User Tier</DialogTitle>
          <DialogDescription>
            Change subscription tier for this user. This will take effect immediately.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* User Info */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">User</div>
            <div className="text-base font-semibold text-gray-900">{user.email}</div>
          </div>

          {/* Current Tier */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Current Tier</div>
            <Badge className={getTierBadgeColor(user.tier)}>{user.tier}</Badge>
          </div>

          {/* New Tier Selection */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">New Tier</div>
            <Select
              value={selectedTier || undefined}
              onValueChange={(value: any) => {
                setSelectedTier(value);
                setShowConfirm(false);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select new tier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FREE">FREE</SelectItem>
                <SelectItem value="PRO">PRO</SelectItem>
                <SelectItem value="PREMIUM">PREMIUM</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Confirmation Message */}
          {selectedTier && selectedTier !== user.tier && !showConfirm && (
            <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-yellow-800">
                <strong>Confirm:</strong> Upgrade {user.email} from{' '}
                <strong>{user.tier}</strong> to <strong>{selectedTier}</strong>?
              </div>
            </div>
          )}

          {selectedTier === user.tier && (
            <div className="text-sm text-gray-500 italic">
              User is already on {user.tier} tier.
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (!showConfirm && selectedTier && selectedTier !== user.tier) {
                setShowConfirm(true);
                handleSubmit();
              }
            }}
            disabled={!selectedTier || selectedTier === user.tier || loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {loading ? 'Updating...' : 'Confirm Upgrade'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
