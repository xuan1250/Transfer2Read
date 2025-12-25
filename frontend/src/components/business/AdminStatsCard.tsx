/**
 * AdminStatsCard Component
 *
 * Displays system-wide statistics for admin dashboard.
 * Shows total users, conversions, active jobs, and monthly conversions.
 */
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, FileText, Activity, Calendar } from 'lucide-react';
import { SystemStats } from '@/types/admin';

interface AdminStatsCardProps {
  stats: SystemStats | null;
  loading: boolean;
}

export default function AdminStatsCard({ stats, loading }: AdminStatsCardProps) {
  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users ?? 0,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Total Conversions',
      value: stats?.total_conversions ?? 0,
      icon: FileText,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Active Jobs',
      value: stats?.active_jobs ?? 0,
      icon: Activity,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: 'Monthly Conversions',
      value: stats?.monthly_conversions ?? 0,
      icon: Calendar,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {statCards.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <Icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-8 bg-gray-200 animate-pulse rounded" />
              ) : (
                <div className="text-2xl font-bold text-gray-900">
                  {stat.value.toLocaleString()}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
