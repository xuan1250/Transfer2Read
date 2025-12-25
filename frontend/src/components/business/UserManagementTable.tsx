/**
 * UserManagementTable Component
 *
 * Admin user management table with pagination, search, filters, and sorting.
 * Displays users with email, tier, conversions, login dates, and actions.
 */
'use client';

import { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AdminUser, UserListParams } from '@/types/admin';
import { Search, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-react';

interface UserManagementTableProps {
  users: AdminUser[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  loading: boolean;
  onParamsChange: (params: UserListParams) => void;
  onUpgradeTier: (user: AdminUser) => void;
}

export default function UserManagementTable({
  users,
  total,
  page,
  pageSize,
  totalPages,
  loading,
  onParamsChange,
  onUpgradeTier,
}: UserManagementTableProps) {
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState<'ALL' | 'FREE' | 'PRO' | 'PREMIUM'>('ALL');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onParamsChange({
        page: 1,
        page_size: pageSize,
        search: search || undefined,
        tier_filter: tierFilter,
        sort_by: sortBy as any,
        sort_order: sortOrder,
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  // Update when filters or sorting change
  useEffect(() => {
    onParamsChange({
      page: 1,
      page_size: pageSize,
      search: search || undefined,
      tier_filter: tierFilter,
      sort_by: sortBy as any,
      sort_order: sortOrder,
    });
  }, [tierFilter, sortBy, sortOrder]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const handlePageChange = (newPage: number) => {
    onParamsChange({
      page: newPage,
      page_size: pageSize,
      search: search || undefined,
      tier_filter: tierFilter,
      sort_by: sortBy as any,
      sort_order: sortOrder,
    });
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

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const SortIcon = ({ column }: { column: string }) => {
    if (sortBy !== column) return null;
    return sortOrder === 'asc' ? (
      <ArrowUp className="ml-1 h-4 w-4 inline" />
    ) : (
      <ArrowDown className="ml-1 h-4 w-4 inline" />
    );
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={tierFilter} onValueChange={(value: any) => setTierFilter(value)}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="Filter by tier" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Tiers</SelectItem>
            <SelectItem value="FREE">FREE</SelectItem>
            <SelectItem value="PRO">PRO</SelectItem>
            <SelectItem value="PREMIUM">PREMIUM</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('email')}
              >
                Email <SortIcon column="email" />
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('tier')}
              >
                Tier <SortIcon column="tier" />
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('conversions')}
              >
                Conversions <SortIcon column="conversions" />
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('last_login')}
              >
                Last Login <SortIcon column="last_login" />
              </TableHead>
              <TableHead
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleSort('created_at')}
              >
                Created <SortIcon column="created_at" />
              </TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 5 }).map((_, idx) => (
                <TableRow key={idx}>
                  <TableCell colSpan={6}>
                    <div className="h-6 bg-gray-200 animate-pulse rounded" />
                  </TableCell>
                </TableRow>
              ))
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                  No users found
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.email}</TableCell>
                  <TableCell>
                    <Badge className={getTierBadgeColor(user.tier)}>{user.tier}</Badge>
                  </TableCell>
                  <TableCell>{user.total_conversions}</TableCell>
                  <TableCell>{formatDate(user.last_login)}</TableCell>
                  <TableCell>{formatDate(user.created_at)}</TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onUpgradeTier(user)}
                    >
                      Upgrade Tier
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Showing {users.length > 0 ? (page - 1) * pageSize + 1 : 0} to{' '}
          {Math.min(page * pageSize, total)} of {total} users
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 1 || loading}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Previous
          </Button>
          <div className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handlePageChange(page + 1)}
            disabled={page === totalPages || loading}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}
