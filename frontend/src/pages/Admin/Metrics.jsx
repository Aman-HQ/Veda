import { useEffect, useState } from 'react';
import api from '../../services/api';
import { 
  Activity, 
  Clock, 
  Cpu, 
  HardDrive, 
  MessageSquare, 
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Users,
  Zap
} from 'lucide-react';
import { format } from 'date-fns';

export default function AdminMetrics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchMetrics();
    
    // Auto-refresh every 30 seconds
    const interval = autoRefresh ? setInterval(() => {
      fetchMetrics();
    }, 30000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/admin/metrics');
      setMetrics(response.data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  const formatUptime = (seconds) => {
    if (!seconds) return '0m';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusColor = (value, thresholds) => {
    if (value >= thresholds.critical) return 'bg-red-600';
    if (value >= thresholds.warning) return 'bg-orange-500';
    return 'bg-green-600';
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-full min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-slate-600 dark:text-slate-400 font-medium">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl p-6 shadow-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" size={24} />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">Failed to Load Metrics</h3>
              <p className="text-red-800 dark:text-red-200">{error}</p>
              <button 
                onClick={fetchMetrics}
                className="mt-4 px-6 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium shadow-sm flex items-center gap-2"
              >
                <RefreshCw size={18} />
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Real-Time Metrics</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">Live system performance and activity monitoring</p>
          {lastUpdated && (
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-2 flex items-center gap-1.5">
              <Clock size={12} />
              Last updated: {format(lastUpdated, 'HH:mm:ss')}
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-3 flex-wrap">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-0"
            />
            <span className="font-medium">Auto-refresh (30s)</span>
          </label>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-sm hover:shadow-md"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            Refresh Now
          </button>
        </div>
      </div>

      {/* Uptime Hero Card */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl shadow-2xl">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative px-8 py-10">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="text-white/90" size={24} />
                <p className="text-white/90 text-sm font-semibold uppercase tracking-wide">System Uptime</p>
              </div>
              <p className="text-5xl md:text-6xl font-bold text-white mb-3">
                {formatUptime(metrics?.uptime?.seconds || 0)}
              </p>
              <p className="text-white/80 text-sm font-medium">
                Started: {metrics?.uptime?.started_at ? format(new Date(metrics.uptime.started_at), 'MMM d, yyyy HH:mm') : 'N/A'}
              </p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm p-6 rounded-2xl border-2 border-white/30 shadow-xl">
              <Clock size={56} className="text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Activity Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2">Active Conversations</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                {metrics?.conversations?.active_last_24h || 0}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">Last 24 hours</p>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-900/20 p-4 rounded-xl">
              <MessageSquare className="text-emerald-600 dark:text-emerald-400" size={28} />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2">Messages Today</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                {metrics?.messages?.today || 0}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">Since midnight</p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl">
              <TrendingUp className="text-blue-600 dark:text-blue-400" size={28} />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2">Active Users (24h)</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                {metrics?.users?.active_last_24h || 0}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">Unique users</p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-xl">
              <Users className="text-purple-600 dark:text-purple-400" size={28} />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2">Flagged (24h)</p>
              <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                {metrics?.messages?.flagged_last_24h || 0}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-2">
                Total: {metrics?.messages?.flagged_total || 0}
              </p>
            </div>
            <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-xl">
              <AlertCircle className="text-orange-600 dark:text-orange-400" size={28} />
            </div>
          </div>
        </div>
      </div>

      {/* System Resources */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-100 dark:bg-indigo-900/30 p-2 rounded-lg">
              <Activity className="text-indigo-600 dark:text-indigo-400" size={20} />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">System Resources</h2>
          </div>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Process Metrics */}
            <div className="space-y-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></div>
                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Application Process
                </h3>
              </div>
              
              {/* Memory Usage */}
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                    <HardDrive size={18} className="text-slate-500 dark:text-slate-400" />
                    Memory Usage
                  </span>
                  <div className="text-right">
                    <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
                      {metrics?.system_resources?.process?.memory_mb?.toFixed(1) || '0.0'} MB
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-500 ml-2">
                      ({metrics?.system_resources?.process?.memory_percent?.toFixed(1) || '0.0'}%)
                    </span>
                  </div>
                </div>
                <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${getStatusColor(
                      metrics?.system_resources?.process?.memory_percent || 0,
                      { warning: 70, critical: 90 }
                    )}`}
                    style={{ width: `${Math.min(metrics?.system_resources?.process?.memory_percent || 0, 100)}%` }}
                  />
                </div>
              </div>
              
              {/* CPU Usage */}
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                    <Cpu size={18} className="text-slate-500 dark:text-slate-400" />
                    CPU Usage
                  </span>
                  <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {metrics?.system_resources?.process?.cpu_percent?.toFixed(1) || '0.0'}%
                  </span>
                </div>
                <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${getStatusColor(
                      metrics?.system_resources?.process?.cpu_percent || 0,
                      { warning: 60, critical: 85 }
                    )}`}
                    style={{ width: `${Math.min(metrics?.system_resources?.process?.cpu_percent || 0, 100)}%` }}
                  />
                </div>
              </div>
              
              {/* Threads */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Threads</span>
                  <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {metrics?.system_resources?.process?.threads || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* System Metrics */}
            <div className="space-y-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1 h-6 bg-gradient-to-b from-emerald-500 to-teal-500 rounded-full"></div>
                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  System Overall
                </h3>
              </div>
              
              {/* System Memory */}
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                    <HardDrive size={18} className="text-slate-500 dark:text-slate-400" />
                    System Memory
                  </span>
                  <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {metrics?.system_resources?.system?.memory_percent?.toFixed(1) || '0.0'}%
                  </span>
                </div>
                <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden mb-3">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${getStatusColor(
                      metrics?.system_resources?.system?.memory_percent || 0,
                      { warning: 75, critical: 90 }
                    )}`}
                    style={{ width: `${Math.min(metrics?.system_resources?.system?.memory_percent || 0, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400">
                  <span>
                    Available: <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {metrics?.system_resources?.system?.memory_available_gb?.toFixed(2) || '0.00'} GB
                    </span>
                  </span>
                  <span>
                    Total: <span className="font-semibold text-slate-700 dark:text-slate-300">
                      {metrics?.system_resources?.system?.memory_total_gb?.toFixed(2) || '0.00'} GB
                    </span>
                  </span>
                </div>
              </div>
              
              {/* System CPU */}
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                    <Cpu size={18} className="text-slate-500 dark:text-slate-400" />
                    System CPU
                  </span>
                  <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {metrics?.system_resources?.system?.cpu_percent?.toFixed(1) || '0.0'}%
                  </span>
                </div>
                <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${getStatusColor(
                      metrics?.system_resources?.system?.cpu_percent || 0,
                      { warning: 70, critical: 90 }
                    )}`}
                    style={{ width: `${Math.min(metrics?.system_resources?.system?.cpu_percent || 0, 100)}%` }}
                  />
                </div>
              </div>
              
              {/* CPU Cores */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-400">CPU Cores</span>
                  <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {metrics?.system_resources?.system?.cpu_count || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Timestamp Footer */}
      <div className="flex items-center justify-center gap-2 py-4">
        <Clock size={14} className="text-slate-400 dark:text-slate-500" />
        <p className="text-xs text-slate-500 dark:text-slate-500 font-medium">
          Data collected at: {metrics?.timestamp ? format(new Date(metrics.timestamp), 'MMM d, yyyy HH:mm:ss') : 'N/A'}
        </p>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Activity className="text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-1">Real-Time Monitoring</p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Metrics are collected in real-time from the application server. 
              Resource usage thresholds: <span className="font-semibold">Green (&lt;70%)</span>, <span className="font-semibold text-orange-600">Warning (70-85%)</span>, <span className="font-semibold text-red-600">Critical (&gt;85%)</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
