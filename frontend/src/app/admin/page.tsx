/**
 * Admin Dashboard Page
 *
 * Protected admin route for system monitoring and user management.
 * Displays system statistics, user list with filters, and tier upgrade functionality.
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import AdminStatsCard from '@/components/business/AdminStatsCard';
import UserManagementTable from '@/components/business/UserManagementTable';
import UpgradeTierModal from '@/components/business/UpgradeTierModal';
import { getAdminStats, getAdminUsers, updateUserTier } from '@/lib/api-client';
import { SystemStats, UserListParams, AdminUser } from '@/types/admin';

export default function AdminDashboard() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  // User management table state
  const [userParams, setUserParams] = useState<UserListParams>({
    page: 1,
    page_size: 20,
    tier_filter: 'ALL',
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  // Tier upgrade modal state
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  // Initialize Supabase client
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  // Check authentication and admin status
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          router.push('/auth/signin');
          return;
        }

        setAccessToken(session.access_token);

        // Check if user is superuser
        const isSuperuser = session.user.user_metadata?.is_superuser === true;

        if (!isSuperuser) {
          router.push('/403');
          return;
        }

        setLoading(false);
      } catch (error) {
        console.error('Auth check failed:', error);
        router.push('/auth/signin');
      }
    };

    checkAuth();
  }, [router, supabase]);

  // Fetch system stats
  const { data: stats, isLoading: statsLoading } = useQuery<SystemStats>({
    queryKey: ['adminStats'],
    queryFn: async () => {
      if (!accessToken) throw new Error('No access token');
      return getAdminStats(accessToken);
    },
    enabled: !!accessToken && !loading,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch users
  const {
    data: usersData,
    isLoading: usersLoading,
    refetch: refetchUsers,
  } = useQuery({
    queryKey: ['adminUsers', userParams],
    queryFn: async () => {
      if (!accessToken) throw new Error('No access token');
      return getAdminUsers(accessToken, userParams);
    },
    enabled: !!accessToken && !loading,
  });

  // Handle tier upgrade
  const handleUpgradeTier = async (userId: string, newTier: 'FREE' | 'PRO' | 'PREMIUM') => {
    if (!accessToken) {
      toast.error('Authentication required');
      return;
    }

    try {
      const result = await updateUserTier(accessToken, userId, { tier: newTier });

      toast.success(
        `User upgraded from ${result.old_tier} to ${result.new_tier} successfully!`
      );

      // Refetch users and stats
      await refetchUsers();
      queryClient.invalidateQueries({ queryKey: ['adminStats'] });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to update user tier';
      toast.error(message);
      throw error; // Re-throw to let modal handle loading state
    }
  };

  const handleUpgradeTierClick = (user: AdminUser) => {
    setSelectedUser(user);
    setModalOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="mt-2 text-gray-600">
            System monitoring and user management
          </p>
        </div>

        {/* System Stats */}
        <AdminStatsCard stats={stats || null} loading={statsLoading} />

        {/* User Management */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            User Management
          </h2>
          <UserManagementTable
            users={usersData?.users || []}
            total={usersData?.total || 0}
            page={usersData?.page || 1}
            pageSize={usersData?.page_size || 20}
            totalPages={usersData?.total_pages || 1}
            loading={usersLoading}
            onParamsChange={setUserParams}
            onUpgradeTier={handleUpgradeTierClick}
          />
        </div>

        {/* Upgrade Tier Modal */}
        <UpgradeTierModal
          user={selectedUser}
          open={modalOpen}
          onClose={() => {
            setModalOpen(false);
            setSelectedUser(null);
          }}
          onConfirm={handleUpgradeTier}
        />
      </div>
    </div>
  );
}
