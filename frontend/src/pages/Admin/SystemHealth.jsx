import { useEffect, useState } from 'react';
import api from '../../services/api';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw,
  Brain,
  Database,
  Shield,
  Clock,
  Zap,
  Activity
} from 'lucide-react';
import { format } from 'date-fns';

export default function AdminSystemHealth() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  useEffect(() => {
    fetchHealth();
    
    // Auto-refresh every 60 seconds if enabled
    const interval = autoRefresh ? setInterval(() => {
      fetchHealth();
    }, 60000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/admin/system/health');
      setHealth(response.data);
      setLastChecked(new Date());
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load system health');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return { 
          bg: 'bg-green-50', 
          text: 'text-green-700', 
          border: 'border-green-300', 
          icon: CheckCircle,
          badge: 'bg-green-100 text-green-800',
          progress: 'bg-green-500'
        };
      case 'degraded':
        return { 
          bg: 'bg-yellow-50', 
          text: 'text-yellow-700', 
          border: 'border-yellow-300', 
          icon: AlertTriangle,
          badge: 'bg-yellow-100 text-yellow-800',
          progress: 'bg-yellow-500'
        };
      case 'unhealthy':
        return { 
          bg: 'bg-red-50', 
          text: 'text-red-700', 
          border: 'border-red-300', 
          icon: XCircle,
          badge: 'bg-red-100 text-red-800',
          progress: 'bg-red-500'
        };
      default:
        return { 
          bg: 'bg-gray-50', 
          text: 'text-gray-700', 
          border: 'border-gray-300', 
          icon: AlertTriangle,
          badge: 'bg-gray-100 text-gray-800',
          progress: 'bg-gray-500'
        };
    }
  };

  const getOverallStatusGradient = (status) => {
    switch (status) {
      case 'healthy':
        return 'from-emerald-500 via-green-500 to-teal-600';
      case 'degraded':
        return 'from-yellow-500 via-orange-500 to-amber-600';
      case 'unhealthy':
        return 'from-red-500 via-rose-500 to-pink-600';
      default:
        return 'from-gray-500 via-slate-500 to-gray-600';
    }
  };

  if (loading && !health) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-20">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
        <p className="text-gray-600 font-medium">Running health diagnostics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-8">
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="bg-red-100 p-3 rounded-full">
              <XCircle className="text-red-600" size={24} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-900 mb-2">Health Check Failed</h3>
              <p className="text-red-800">{error}</p>
              <button 
                onClick={fetchHealth}
                className="mt-4 flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <RefreshCw size={18} />
                Retry Health Check
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const overallGradient = getOverallStatusGradient(health?.overall_status);

  const components = [
    {
      name: 'LLM Provider',
      icon: Brain,
      data: health?.components?.llm_provider,
      description: 'Language model service for intelligent chat responses',
      details: health?.components?.llm_provider?.details
    },
    {
      name: 'RAG Pipeline',
      icon: Database,
      data: health?.components?.rag_pipeline,
      description: 'Retrieval augmented generation and vector search system',
      details: health?.components?.rag_pipeline?.details
    },
    {
      name: 'Moderation Service',
      icon: Shield,
      data: health?.components?.moderation_service,
      description: 'Content filtering, safety checks, and policy enforcement',
      details: health?.components?.moderation_service?.details
    }
  ];

  // Calculate health score (percentage of healthy components)
  const healthyCount = components.filter(c => c.data?.status === 'healthy').length;
  const healthScore = Math.round((healthyCount / components.length) * 100);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
          <p className="text-gray-600 mt-1">Component status and diagnostic information</p>
          {lastChecked && (
            <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
              <Clock size={14} />
              <span>Last checked: {format(lastChecked, 'MMM d, yyyy HH:mm:ss')}</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
            />
            Auto-refresh (60s)
          </label>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm hover:shadow-md"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Checking...' : 'Run Health Check'}
          </button>
        </div>
      </div>

      {/* Overall Status Hero Card */}
      <div className={`bg-gradient-to-br ${overallGradient} rounded-xl shadow-2xl p-8 text-white relative overflow-hidden`}>
        {/* Decorative background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-64 h-64 bg-white rounded-full -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full translate-x-1/3 translate-y-1/3"></div>
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-white bg-opacity-20 p-3 rounded-lg backdrop-blur-sm">
                  <Activity size={32} />
                </div>
                <div>
                  <p className="text-white text-opacity-90 text-sm font-medium uppercase tracking-wider">
                    Overall System Status
                  </p>
                  <p className="text-5xl font-bold capitalize mt-1">
                    {health?.overall_status || 'Unknown'}
                  </p>
                </div>
              </div>
              
              {health?.checked_at && (
                <p className="text-white text-opacity-75 text-sm">
                  Diagnostic completed at {format(new Date(health.checked_at), 'MMM d, yyyy HH:mm:ss')}
                </p>
              )}
            </div>
            
            <div className="flex flex-col items-center gap-4">
              <div className="relative w-32 h-32">
                {/* Circular progress indicator */}
                <svg className="transform -rotate-90 w-32 h-32">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    className="text-white opacity-20"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${2 * Math.PI * 56}`}
                    strokeDashoffset={`${2 * Math.PI * 56 * (1 - healthScore / 100)}`}
                    className="text-white transition-all duration-1000"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold">{healthScore}%</span>
                  <span className="text-xs text-white text-opacity-75">Health Score</span>
                </div>
              </div>
              
              <div className="flex gap-2">
                {components.map((comp) => (
                  <div
                    key={comp.name}
                    className={`w-3 h-3 rounded-full ${
                      comp.data?.status === 'healthy' ? 'bg-white' :
                      comp.data?.status === 'degraded' ? 'bg-yellow-300' :
                      'bg-red-300'
                    }`}
                    title={`${comp.name}: ${comp.data?.status}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Component Health Cards */}
      <div className="grid grid-cols-1 gap-6">
        {components.map((component) => {
          const statusColors = getStatusColor(component.data?.status);
          const StatusIcon = statusColors.icon;
          const ComponentIcon = component.icon;
          
          return (
            <div 
              key={component.name}
              className={`bg-white rounded-xl shadow-lg border-2 ${statusColors.border} overflow-hidden hover:shadow-xl transition-shadow duration-300`}
            >
              {/* Component Header */}
              <div className={`${statusColors.bg} px-6 py-4 border-b-2 ${statusColors.border}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`${statusColors.badge} p-3 rounded-lg`}>
                      <ComponentIcon className={statusColors.text} size={28} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">{component.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">{component.description}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <span className={`${statusColors.badge} px-4 py-2 rounded-full text-sm font-semibold uppercase tracking-wide flex items-center gap-2`}>
                      <StatusIcon size={18} />
                      {component.data?.status || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Component Body */}
              <div className="p-6">
                {/* Status Message */}
                {component.data?.message && (
                  <div className={`mb-6 p-4 rounded-lg border-l-4 ${
                    component.data.status === 'healthy' ? 'bg-green-50 border-green-500' :
                    component.data.status === 'degraded' ? 'bg-yellow-50 border-yellow-500' :
                    'bg-red-50 border-red-500'
                  }`}>
                    <div className="flex items-start gap-3">
                      <StatusIcon 
                        className={component.data.status === 'healthy' ? 'text-green-600' :
                                  component.data.status === 'degraded' ? 'text-yellow-600' :
                                  'text-red-600'}
                        size={20}
                      />
                      <div className="flex-1">
                        <p className={`text-sm font-medium ${
                          component.data.status === 'healthy' ? 'text-green-900' :
                          component.data.status === 'degraded' ? 'text-yellow-900' :
                          'text-red-900'
                        }`}>
                          {component.data.message}
                        </p>
                        
                        {component.data.error && (
                          <div className="mt-2 p-3 bg-white rounded border border-red-200">
                            <p className="text-xs font-mono text-red-700">{component.data.error}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Component Details */}
                {component.details && Object.keys(component.details).length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <Zap size={16} className="text-blue-600" />
                      Component Details
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(component.details).map(([key, value]) => (
                        <div 
                          key={key}
                          className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-600 capitalize">
                              {key.replace(/_/g, ' ')}
                            </span>
                            <span className="text-sm font-semibold text-gray-900">
                              {typeof value === 'boolean' ? (
                                value ? (
                                  <span className="flex items-center gap-1 text-green-600">
                                    <CheckCircle size={16} />
                                    Yes
                                  </span>
                                ) : (
                                  <span className="flex items-center gap-1 text-red-600">
                                    <XCircle size={16} />
                                    No
                                  </span>
                                )
                              ) : typeof value === 'number' ? (
                                value.toLocaleString()
                              ) : (
                                String(value)
                              )}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* No details available */}
                {(!component.details || Object.keys(component.details).length === 0) && !component.data?.message && (
                  <div className="text-center py-8 text-gray-400">
                    <Activity size={32} className="mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No additional diagnostic information available</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Health Check Information Panel */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="bg-blue-100 p-3 rounded-lg">
            <AlertTriangle className="text-blue-600" size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">About Health Diagnostics</h3>
            <div className="text-sm text-blue-800 space-y-2">
              <p>
                <strong>Healthy:</strong> All components are operational and functioning within normal parameters. 
                The system is ready to handle production workloads.
              </p>
              <p>
                <strong>Degraded:</strong> Some components are experiencing issues or operating with reduced capacity. 
                Core functionality remains available but some features may be limited or slower than normal.
              </p>
              <p>
                <strong>Unhealthy:</strong> Critical failures detected in one or more components. 
                Immediate attention required to restore full system functionality.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Timestamp Footer */}
      <div className="text-center text-xs text-gray-500 pb-4">
        <div className="flex items-center justify-center gap-2">
          <Clock size={14} />
          <span>
            Health diagnostics performed at: {health?.checked_at ? format(new Date(health.checked_at), 'MMMM d, yyyy \'at\' HH:mm:ss') : 'Unknown'}
          </span>
        </div>
      </div>
    </div>
  );
}
