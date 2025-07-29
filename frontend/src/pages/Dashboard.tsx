import React from 'react';
import { useQuery } from 'react-query';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  ClockIcon,
  CheckBadgeIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { dashboardAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const { data: metrics, isLoading: metricsLoading } = useQuery(
    'dashboard-metrics',
    () => dashboardAPI.getMetrics().then(res => res.data),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const { data: recentActivity } = useQuery(
    'recent-activity',
    () => dashboardAPI.getRecentActivity().then(res => res.data),
    {
      refetchInterval: 60000, // Refetch every minute
    }
  );

  const kpiCards = [
    {
      title: 'Quotes Generated',
      value: metrics?.quotes_generated || 0,
      change: metrics?.quotes_generated_change || 0,
      icon: DocumentTextIcon,
      color: 'primary',
    },
    {
      title: 'Total Revenue',
      value: `$${(metrics?.total_revenue || 0).toLocaleString()}`,
      change: metrics?.total_revenue_change || 0,
      icon: CurrencyDollarIcon,
      color: 'success',
    },
    {
      title: 'Avg. Processing Time',
      value: `${Math.round(metrics?.avg_processing_time || 0)} min`,
      change: metrics?.avg_processing_time_change || 0,
      icon: ClockIcon,
      color: 'warning',
      inverse: true, // Lower is better for processing time
    },
    {
      title: 'Accuracy Rate',
      value: `${Math.round((metrics?.accuracy_rate || 0) * 100)}%`,
      change: metrics?.accuracy_rate_change || 0,
      icon: CheckBadgeIcon,
      color: 'primary',
    },
  ];

  const formatChange = (change: number, inverse: boolean = false) => {
    const isPositive = inverse ? change < 0 : change > 0;
    const icon = isPositive ? ArrowTrendingUpIcon : ArrowTrendingDownIcon;
    const colorClass = isPositive ? 'text-success-600' : 'text-error-600';
    
    return {
      icon,
      colorClass,
      text: `${Math.abs(change).toFixed(1)}%`,
    };
  };

  if (metricsLoading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-6">
              <div className="h-4 bg-gray-200 rounded mb-4"></div>
              <div className="h-8 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">
          Manufacturing RFQ Intelligence Platform
        </h2>
        <p className="mt-2 text-gray-600">
          AI-powered quote management and analytics dashboard
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((card, index) => {
          const changeInfo = formatChange(card.change, card.inverse);
          const ChangeIcon = changeInfo.icon;
          
          return (
            <div key={index} className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{card.title}</p>
                  <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
                </div>
                <div className={`p-3 rounded-full bg-${card.color}-100`}>
                  <card.icon className={`h-6 w-6 text-${card.color}-600`} />
                </div>
              </div>
              <div className="mt-4 flex items-center">
                <ChangeIcon className={`h-4 w-4 ${changeInfo.colorClass}`} />
                <span className={`ml-1 text-sm ${changeInfo.colorClass}`}>
                  {changeInfo.text}
                </span>
                <span className="ml-1 text-sm text-gray-500">from last period</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pipeline Status */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6 lg:col-span-2">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Quote Pipeline Status
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Pending</span>
              <div className="flex items-center">
                <span className="status-pending">{metrics?.quotes_pending || 0}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Approved</span>
              <div className="flex items-center">
                <span className="status-approved">{metrics?.quotes_approved || 0}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Rejected</span>
              <div className="flex items-center">
                <span className="status-rejected">{metrics?.quotes_rejected || 0}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Quick Stats
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">New Clients</span>
                <span className="text-sm font-medium text-gray-900">
                  {metrics?.new_clients_this_month || 0}
                </span>
              </div>
              <p className="text-xs text-gray-500">This month</p>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">AI Confidence</span>
                <span className="text-sm font-medium text-gray-900">
                  {Math.round((metrics?.accuracy_rate || 0) * 100)}%
                </span>
              </div>
              <p className="text-xs text-gray-500">Average prediction accuracy</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-4">
          {recentActivity?.activities?.slice(0, 5).map((activity: any, index: number) => (
            <div key={index} className="flex items-center justify-between py-2">
              <div className="flex-1">
                <p className="text-sm text-gray-900">{activity.description}</p>
                <p className="text-xs text-gray-500">
                  {new Date(activity.timestamp).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`status-${activity.status}`}>
                  {activity.status}
                </span>
                {activity.value && (
                  <span className="text-sm font-medium text-gray-900">
                    ${activity.value.toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          )) || (
            <p className="text-sm text-gray-500">No recent activity</p>
          )}
        </div>
      </div>

      {/* AI Processing Insights */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          AI Processing Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-600">
              {Math.round((metrics?.accuracy_rate || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Model Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-success-600">
              {Math.round(metrics?.avg_processing_time || 0)}min
            </div>
            <div className="text-sm text-gray-600">Avg Processing Time</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-warning-600">
              {metrics?.quotes_generated || 0}
            </div>
            <div className="text-sm text-gray-600">Files Processed</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;