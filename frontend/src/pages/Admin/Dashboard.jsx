import { useEffect, useState, useRef, useCallback, useMemo, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, MessageSquare, AlertTriangle, Activity, TrendingUp, Calendar, RefreshCw, MessageCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '../../services/api';

// Memoized chart component to prevent re-renders from countdown updates
const ActivityChart = memo(({ chartData }) => {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <TrendingUp size={20} className="text-indigo-600 dark:text-indigo-400" />
          Activity Trends
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Daily metrics over the selected time period</p>
      </div>
      <div className="p-6">
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
            <XAxis 
              dataKey="date" 
              className="text-xs text-slate-600 dark:text-slate-400"
              tick={{ fill: 'currentColor' }}
              stroke="currentColor"
            />
            <YAxis 
              className="text-xs text-slate-600 dark:text-slate-400"
              tick={{ fill: 'currentColor' }}
              stroke="currentColor"
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              }}
              labelStyle={{ color: '#1e293b', fontWeight: 600 }}
            />
            <Legend 
              wrapperStyle={{
                paddingTop: '20px',
              }}
              iconType="line"
            />
            <Line 
              type="monotone" 
              dataKey="messages" 
              stroke="#8b5cf6" 
              strokeWidth={2.5}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Messages"
            />
            <Line 
              type="monotone" 
              dataKey="conversations" 
              stroke="#10b981" 
              strokeWidth={2.5}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Conversations"
            />
            <Line 
              type="monotone" 
              dataKey="users" 
              stroke="#3b82f6" 
              strokeWidth={2.5}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Active Users"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});

ActivityChart.displayName = 'ActivityChart';

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [previousStats, setPreviousStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(7); // Default 7 days
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [refreshCountdown, setRefreshCountdown] = useState(1800); // 30 minutes in seconds
  const [chartData, setChartData] = useState([]);
  const refreshIntervalRef = useRef(null);
  const countdownIntervalRef = useRef(null);

  const fetchStats = useCallback(async () => {
    try {
      // Fetch current period stats
      const response = await api.get('/api/admin/stats', { 
        params: { days: timeRange } 
      });
      
      // Fetch previous period stats for trend calculation
      const prevResponse = await api.get('/api/admin/stats', { 
        params: { days: timeRange * 2 } // Get double the period for comparison
      });
      
      // Transform backend response
      const data = response.data;
      const prevData = prevResponse.data;
      const overview = data.overview || {};
      const moderation = data.moderation || {};
      const prevOverview = prevData.overview || {};
      const prevModeration = prevData.moderation || {};
      const dailyActivity = data.daily_activity || [];
      
      // Get today's data from the last entry in daily_activity
      const todayData = dailyActivity.length > 0 ? dailyActivity[dailyActivity.length - 1] : {};
      
      const currentStats = {
        // Overview stats
        total_users: overview.total_users || 0,
        total_conversations: overview.total_conversations || 0,
        total_messages: overview.total_messages || 0,
        
        // Moderation stats
        flagged_messages: moderation.total_flags || 0,
        pending_reviews: moderation.needs_review || 0, // Items that need review
        
        // Today's activity (from actual today's data)
        active_users_today: todayData.active_users || 0,
        conversations_today: todayData.conversations || 0,
        messages_today: todayData.messages || 0,
        avg_messages_per_conversation: overview.avg_messages_per_conversation || 0,
        
        // Raw data for reference
        raw_overview: overview,
        raw_moderation: moderation,
        time_range: data.time_range,
        daily_activity: dailyActivity,
      };
      
      // Store previous period stats for trend calculation
      const prevStats = {
        total_users: prevOverview.total_users || 0,
        total_conversations: prevOverview.total_conversations || 0,
        total_messages: prevOverview.total_messages || 0,
        flagged_messages: prevModeration.total_flags || 0,
      };
      
      setStats(currentStats);
      setPreviousStats(prevStats);
      setLastRefresh(new Date());
      setRefreshCountdown(1800); // Reset to 30 minutes
      
      // Transform daily_activity to chart format
      const chartData = dailyActivity.map(day => ({
        date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        messages: day.messages,
        conversations: day.conversations,
        users: day.active_users,
      }));
      setChartData(chartData);
      
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  }, [timeRange]); // Only depend on timeRange, not loading

  useEffect(() => {
    fetchStats();
    
    // Setup auto-refresh every 30 minutes
    refreshIntervalRef.current = setInterval(() => {
      fetchStats();
    }, 1800000); // 30 minutes = 1800000 milliseconds
    
    // Setup countdown timer
    countdownIntervalRef.current = setInterval(() => {
      setRefreshCountdown(prev => {
        const newValue = prev <= 1 ? 1800 : prev - 1;
        // Only update state when value actually changes (every second is fine for display)
        // But we'll optimize the component to not re-render the chart
        return newValue;
      });
    }, 1000);
    
    // Cleanup intervals on unmount or timeRange change
    return () => {
      if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, [fetchStats]); // Depend on fetchStats which depends on timeRange

  // Calculate trend percentage
  const calculateTrend = (current, previous) => {
    if (!previous || previous === 0) return { value: 0, isUp: false };
    
    // For double period comparison, we need to calculate the trend for the current period
    // Previous period would be (total_from_double_period - current_period)
    const previousPeriodValue = previous - current;
    if (previousPeriodValue === 0) return { value: 0, isUp: false };
    
    const percentChange = ((current - previousPeriodValue) / previousPeriodValue) * 100;
    return {
      value: Math.abs(percentChange).toFixed(1),
      isUp: percentChange >= 0
    };
  };
  
  // Manual refresh handler
  const handleManualRefresh = () => {
    fetchStats();
    // Reset intervals
    if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    
    refreshIntervalRef.current = setInterval(() => {
      fetchStats();
    }, 1800000); // 30 minutes
    
    countdownIntervalRef.current = setInterval(() => {
      setRefreshCountdown(prev => {
        if (prev <= 1) return 1800; // Reset to 30 minutes
        return prev - 1;
      });
    }, 1000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-slate-600 dark:text-slate-400 mt-4 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" size={24} />
          <div className="flex-1">
            <h3 className="text-red-900 dark:text-red-100 font-semibold mb-1">Error Loading Dashboard</h3>
            <p className="text-red-800 dark:text-red-200">{error}</p>
            <button 
              onClick={fetchStats}
              className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const usersTrend = previousStats ? calculateTrend(stats?.total_users || 0, previousStats.total_users) : { value: 0, isUp: false };
  const conversationsTrend = previousStats ? calculateTrend(stats?.total_conversations || 0, previousStats.total_conversations) : { value: 0, isUp: false };
  const messagesTrend = previousStats ? calculateTrend(stats?.total_messages || 0, previousStats.total_messages) : { value: 0, isUp: false };
  const flaggedTrend = previousStats ? calculateTrend(stats?.flagged_messages || 0, previousStats.flagged_messages) : { value: 0, isUp: false };
  
  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'blue',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
      iconColor: 'text-blue-600 dark:text-blue-400',
      borderColor: 'border-blue-200 dark:border-blue-800',
      trend: `${usersTrend.isUp ? '+' : '-'}${usersTrend.value}%`,
      trendUp: usersTrend.isUp,
    },
    {
      title: 'Total Conversations',
      value: stats?.total_conversations || 0,
      icon: MessageSquare,
      color: 'green',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      iconColor: 'text-green-600 dark:text-green-400',
      borderColor: 'border-green-200 dark:border-green-800',
      trend: `${conversationsTrend.isUp ? '+' : '-'}${conversationsTrend.value}%`,
      trendUp: conversationsTrend.isUp,
    },
    {
      title: 'Total Messages',
      value: stats?.total_messages || 0,
      icon: Activity,
      color: 'purple',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
      iconColor: 'text-purple-600 dark:text-purple-400',
      borderColor: 'border-purple-200 dark:border-purple-800',
      trend: `${messagesTrend.isUp ? '+' : '-'}${messagesTrend.value}%`,
      trendUp: messagesTrend.isUp,
    },
    {
      title: 'Flagged Messages',
      value: stats?.flagged_messages || 0,
      icon: AlertTriangle,
      color: 'red',
      bgColor: 'bg-red-50 dark:bg-red-900/20',
      iconColor: 'text-red-600 dark:text-red-400',
      borderColor: 'border-red-200 dark:border-red-800',
      trend: `${flaggedTrend.isUp ? '+' : '-'}${flaggedTrend.value}%`,
      trendUp: !flaggedTrend.isUp, // Inverted for flagged messages (decrease is good)
    },
  ];

  const todayStats = [
    { label: 'Active Users Today', value: stats?.active_users_today || 0, icon: Users, color: 'text-blue-600 dark:text-blue-400' },
    { label: 'Conversations Today', value: stats?.conversations_today || 0, icon: MessageSquare, color: 'text-green-600 dark:text-green-400' },
    { label: 'Messages Today', value: stats?.messages_today || 0, icon: Activity, color: 'text-purple-600 dark:text-purple-400' },
    { label: 'Avg Messages/Conv', value: stats?.avg_messages_per_conversation?.toFixed(1) || 0, icon: TrendingUp, color: 'text-orange-600 dark:text-orange-400' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Dashboard</h1>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-slate-600 dark:text-slate-400 text-sm">System overview and statistics</p>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Auto-refresh in {Math.floor(refreshCountdown / 60)}m {refreshCountdown % 60}s</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2.5">
          {/* Manual Refresh Button */}
          <button
            onClick={handleManualRefresh}
            className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors duration-200 text-sm font-medium shadow-sm"
            title="Refresh now"
          >
            <RefreshCw size={16} className="text-slate-500 dark:text-slate-400" />
            <span>Refresh</span>
          </button>
          
          {/* Time Range Selector */}
          <div className="flex items-center gap-2 bg-white dark:bg-slate-800 rounded-lg px-3 py-2 border border-slate-200 dark:border-slate-700 shadow-sm">
            <Calendar className="text-slate-400" size={16} />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="bg-transparent border-none focus:outline-none focus:ring-0 text-sm font-medium text-slate-700 dark:text-slate-500 cursor-pointer pr-2"
            >
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
            </select>
          </div>

          {/* Chat Page Button */}
          <button
            onClick={() => navigate('/chat')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors duration-200 text-sm font-medium shadow-sm"
            title="Go to Chat Page"
          >
            <MessageCircle size={16} />
            <span>Chat Page</span>
          </button>
        </div>
      </div>

      {/* Main Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => (
          <div
            key={card.title}
            className={`bg-white dark:bg-slate-800 rounded-xl shadow-sm border ${card.borderColor} p-6 hover:shadow-md transition-all duration-200 animate-in slide-in-from-bottom-4`}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2">{card.title}</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  {card.value.toLocaleString()}
                </p>
                <div className="flex items-center gap-1">
                  <TrendingUp 
                    size={14} 
                    className={card.trendUp ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400 rotate-180'} 
                  />
                  <span className={`text-xs font-medium ${card.trendUp ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {card.trend}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">vs last period</span>
                </div>
              </div>
              <div className={`${card.bgColor} p-3 rounded-xl border ${card.borderColor}`}>
                <card.icon className={card.iconColor} size={24} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Activity Trends Chart */}
      <ActivityChart chartData={chartData} />

      {/* Today's Activity */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800 dark:to-slate-800">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Activity size={20} className="text-indigo-600 dark:text-indigo-400" />
            Today's Activity
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Real-time metrics for today</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {todayStats.map((stat, index) => (
              <div 
                key={stat.label} 
                className="text-center p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-900 transition-colors duration-200 border border-slate-200 dark:border-slate-700 animate-in fade-in"
                style={{ animationDelay: `${(index + 4) * 100}ms` }}
              >
                <stat.icon className={`${stat.color} mx-auto mb-2`} size={24} />
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg overflow-hidden">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-white mb-1 flex items-center gap-2">
            <Activity size={20} />
            Quick Actions
          </h2>
          <p className="text-indigo-100 text-sm mb-4">Navigate to key admin sections</p>
          <div className="flex flex-wrap gap-3">
            <button 
              onClick={() => navigate('/admin/metrics')}
              className="px-4 py-2.5 bg-white dark:bg-white text-indigo-600 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-50 transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
            >
              📊 View Real-Time Metrics
            </button>
            <button 
              onClick={() => navigate('/admin/health')}
              className="px-4 py-2.5 bg-white dark:bg-white text-green-600 rounded-lg hover:bg-green-50 dark:hover:bg-green-50 transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
            >
              ❤️ View System Health
            </button>
            <button 
              onClick={() => navigate('/admin/moderation')}
              className="px-4 py-2.5 bg-white dark:bg-white text-purple-600 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-50 transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
            >
              🛡️ View Moderation Queue
            </button>
            <button 
              onClick={() => navigate('/admin/users')}
              className="px-4 py-2.5 bg-white dark:bg-white text-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-50 transition-all duration-200 font-medium text-sm shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
            >
              👥 Manage Users
            </button>
          </div>
        </div>
      </div>

      {/* System Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">System Status</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400">All systems operational</p>
            </div>
          </div>
          <button 
            onClick={() => navigate('/admin/health')}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
          >
            View Details →
          </button>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
              <AlertTriangle className="text-orange-500" size={20} />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">Pending Reviews</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400">{stats?.pending_reviews || 0} items need attention</p>
            </div>
          </div>
          <button 
            onClick={() => navigate('/admin/moderation?filter=needs-review')}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
          >
            Review Now →
          </button>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <Users className="text-blue-500" size={20} />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">User Activity</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400">{stats?.active_users_today || 0} active users today</p>
            </div>
          </div>
          <button 
            onClick={() => navigate('/admin/users')}
            className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium"
          >
            View Users →
          </button>
        </div>
      </div>

      {/* Footer Info */}
      <div className="text-center text-xs text-slate-500 dark:text-slate-400 py-4">
        <div className="flex items-center justify-center gap-2">
          <span>Last updated: {lastRefresh.toLocaleString()}</span>
          <span>•</span>
          <span>Next refresh in {Math.floor(refreshCountdown / 60)}m {refreshCountdown % 60}s</span>
        </div>
      </div>
    </div>
  );
}
