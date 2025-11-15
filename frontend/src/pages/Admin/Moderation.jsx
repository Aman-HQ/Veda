import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertTriangle, CheckCircle, Eye, ChevronLeft, ChevronRight, RefreshCw, Search, X, Shield, Clock, User } from 'lucide-react';
import { format } from 'date-fns';
import api from '../../services/api';

export default function AdminModeration() {
  const [searchParams] = useSearchParams();
  const [flaggedConversations, setFlaggedConversations] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reloadingRules, setReloadingRules] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [reviewedFilter, setReviewedFilter] = useState(null);
  const [userEmailFilter, setUserEmailFilter] = useState('');
  const [userEmailInput, setUserEmailInput] = useState('');
  const [viewingConversation, setViewingConversation] = useState(null);
  const [resolvingMessages, setResolvingMessages] = useState(new Set());
  const [showEmailMessage, setShowEmailMessage] = useState(false);

  // Check for filter parameter from URL on mount
  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (filterParam === 'needs-review') {
      setReviewedFilter(false); // false = needs review
    }
  }, [searchParams]);

  useEffect(() => {
    fetchFlaggedConversations();
    fetchStats();
  }, [page, reviewedFilter, userEmailFilter]);

  const fetchFlaggedConversations = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: 20 };
      if (reviewedFilter !== null) params.reviewed = reviewedFilter;
      if (userEmailFilter) params.user_email = userEmailFilter;

      const response = await api.get('/api/admin/moderation/flagged', { params });
      console.log('API Response:', response.data); // DEBUG
      console.log('First conversation:', response.data.conversations?.[0]); // DEBUG
      setFlaggedConversations(response.data.conversations || []);
      setTotal(response.data.total);
      setTotalPages(Math.ceil(response.data.total / response.data.page_size));
    } catch (err) {
      console.error('Failed to load flagged conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/api/admin/moderation/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load moderation stats:', err);
    }
  };

  const handleReloadRules = async () => {
    try {
      setReloadingRules(true);
      const response = await api.post('/api/admin/moderation/reload-rules');
      alert(`✅ Rules reloaded successfully!\nLoaded ${response.data.new_rule_count} moderation rules.`);
      fetchStats();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reload moderation rules');
    } finally {
      setReloadingRules(false);
    }
  };

  const handleResolveMessage = async (messageId) => {
    try {
      setResolvingMessages(prev => new Set(prev).add(messageId));
      await api.patch(`/api/admin/moderation/resolve/${messageId}`);
      fetchFlaggedConversations();
      fetchStats();
      
      // Update viewing conversation if open
      if (viewingConversation && viewingConversation.flagged_messages) {
        const updatedMessages = viewingConversation.flagged_messages.map(msg =>
          msg.message_id === messageId ? { ...msg, reviewed: true } : msg
        );
        setViewingConversation({ ...viewingConversation, flagged_messages: updatedMessages });
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to resolve message');
    } finally {
      setResolvingMessages(prev => {
        const newSet = new Set(prev);
        newSet.delete(messageId);
        return newSet;
      });
    }
  };

  const handleMarkAllReviewed = async () => {
    if (!viewingConversation?.flagged_messages) return;
    
    try {
      // Get all unreviewed message IDs
      const unreviewedMessages = viewingConversation.flagged_messages.filter(msg => !msg.reviewed);
      
      if (unreviewedMessages.length === 0) return;

      // Mark all unreviewed messages
      setResolvingMessages(new Set(unreviewedMessages.map(m => m.message_id)));
      
      // Resolve all messages in parallel
      await Promise.all(
        unreviewedMessages.map(msg => 
          api.patch(`/api/admin/moderation/resolve/${msg.message_id}`)
        )
      );
      
      // Update local state
      const updatedMessages = viewingConversation.flagged_messages.map(msg => ({
        ...msg,
        reviewed: true
      }));
      setViewingConversation({ ...viewingConversation, flagged_messages: updatedMessages });
      
      await fetchFlaggedConversations();
      await fetchStats();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to mark all as reviewed');
    } finally {
      setResolvingMessages(new Set());
    }
  };

  const handleSearchEmail = (e) => {
    e.preventDefault();
    setUserEmailFilter(userEmailInput);
    setPage(1);
  };

  const handleClearFilters = () => {
    setUserEmailInput('');
    setUserEmailFilter('');
    setReviewedFilter(null);
    setPage(1);
  };

  if (loading && flaggedConversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-slate-600 dark:text-slate-400 mt-4 text-sm">Loading moderation data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Content Moderation</h1>
          <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
            Review and manage flagged content
          </p>
        </div>
        
        <button
          onClick={handleReloadRules}
          disabled={reloadingRules}
          className="flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200 text-sm font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={18} className={reloadingRules ? 'animate-spin' : ''} />
          {reloadingRules ? 'Reloading...' : 'Reload Rules'}
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">Total Flagged</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">
                  {stats.database_counts?.total_flagged || 0}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">All time</p>
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                <AlertTriangle className="text-red-600 dark:text-red-400" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">Needs Review</p>
                <p className="text-3xl font-bold text-orange-600 dark:text-orange-400 mt-2">
                  {stats.database_counts?.flagged_unreviewed || 0}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Pending action</p>
              </div>
              <div className="bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg">
                <Eye className="text-orange-600 dark:text-orange-400" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">Flagged Today</p>
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">
                  {stats.database_counts?.flagged_today || 0}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Last 24 hours</p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                <AlertTriangle className="text-blue-600 dark:text-blue-400" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">Rules Loaded</p>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-2">
                  {stats.total_rules || 0}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Active rules</p>
              </div>
              <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                <Shield className="text-purple-600 dark:text-purple-400" size={24} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Keywords */}
      {stats?.top_keywords && stats.top_keywords.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
            <AlertTriangle className="text-red-600 dark:text-red-400" size={24} />
            Top Flagged Keywords
          </h2>
          <div className="flex flex-wrap gap-2">
            {stats.top_keywords.map((item) => (
              <span
                key={item.keyword}
                className="px-3 py-1.5 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 rounded-full text-sm font-medium"
              >
                {item.keyword} <span className="text-red-600 dark:text-red-400 font-bold">({item.count})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
        <div className="flex flex-col lg:flex-row gap-3">
          {/* Review Status Filters */}
          <div className="flex gap-2">
            <button
              onClick={() => { setReviewedFilter(null); setPage(1); }}
              className={`px-4 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                reviewedFilter === null
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => { setReviewedFilter(false); setPage(1); }}
              className={`px-4 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                reviewedFilter === false
                  ? 'bg-orange-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              Needs Review
            </button>
            <button
              onClick={() => { setReviewedFilter(true); setPage(1); }}
              className={`px-4 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                reviewedFilter === true
                  ? 'bg-green-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              Reviewed
            </button>
          </div>
          
          {/* User Email Filter */}
          <form onSubmit={handleSearchEmail} className="flex-1 flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" size={18} />
              <input
                type="text"
                placeholder="Filter by user email..."
                value={userEmailInput}
                onChange={(e) => setUserEmailInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 transition-colors"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors text-sm font-medium shadow-sm"
            >
              Search
            </button>
          </form>
          
          {(userEmailFilter || reviewedFilter !== null) && (
            <button
              onClick={handleClearFilters}
              className="px-4 py-2.5 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors text-sm font-medium"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Flagged Conversations Table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  Conversation
                </th>
                <th className="px-6 py-4 text-center text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  Flagged Messages
                </th>
                <th className="px-6 py-4 text-center text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  Latest Flag
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    </div>
                  </td>
                </tr>
              ) : flaggedConversations.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <CheckCircle className="text-green-400 dark:text-green-600" size={48} />
                      <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">No flagged conversations found</p>
                      {(userEmailFilter || reviewedFilter !== null) && (
                        <button
                          onClick={handleClearFilters}
                          className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 text-sm font-medium"
                        >
                          Clear filters to see all
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                flaggedConversations.map((conv) => {
                  // Use backend-provided counts instead of array length (which is filtered)
                  const totalFlagged = conv.total_flagged_count || 0;
                  const unreviewedCount = conv.unreviewed_count || 0;
                  const reviewedCount = conv.reviewed_count || 0;
                  
                  return (
                    <tr key={conv.conversation_id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                            {conv.user_email?.charAt(0).toUpperCase() || '?'}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                              {conv.user_email}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">
                              {totalFlagged} flagged message{totalFlagged !== 1 ? 's' : ''}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="max-w-xs">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                            {conv.title || 'Untitled Conversation'}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            ID: {conv.conversation_id?.slice(0, 8) || 'N/A'}...
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
                            {totalFlagged} total
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        {/* Show status based on active filter */}
                        {reviewedFilter === false && unreviewedCount > 0 ? (
                          // "Needs Review" filter active - show unreviewed count in orange
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">
                            <Eye size={12} />
                            {unreviewedCount} need review
                          </span>
                        ) : reviewedFilter === true && reviewedCount > 0 ? (
                          // "Reviewed" filter active - show reviewed count in green
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
                            <CheckCircle size={12} />
                            {reviewedCount} reviewed
                          </span>
                        ) : reviewedFilter === null ? (
                          // "All" filter - show most relevant status
                          unreviewedCount > 0 ? (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">
                              <Eye size={12} />
                              {unreviewedCount} need review
                            </span>
                          ) : reviewedCount > 0 ? (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
                              <CheckCircle size={12} />
                              {reviewedCount} reviewed
                            </span>
                          ) : (
                            <span className="text-xs text-slate-500 dark:text-slate-400">No status</span>
                          )
                        ) : (
                          <span className="text-xs text-slate-500 dark:text-slate-400">No status</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                          <Clock size={14} className="text-slate-400 dark:text-slate-500" />
                          {conv.flagged_messages?.[0]?.created_at ? 
                            format(new Date(conv.flagged_messages[0].created_at), 'MMM d, HH:mm') : 
                            'N/A'
                          }
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => setViewingConversation(conv)}
                          className="inline-flex items-center gap-2 px-4 py-2 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors text-sm font-medium"
                        >
                          <Eye size={16} />
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && flaggedConversations.length > 0 && (
          <div className="bg-slate-50 dark:bg-slate-900 px-6 py-4 flex items-center justify-between border-t border-slate-200 dark:border-slate-700">
            <div className="text-sm text-slate-700 dark:text-slate-300">
              Showing <span className="font-semibold">{(page - 1) * 20 + 1}</span> to{' '}
              <span className="font-semibold">{Math.min(page * 20, total)}</span> of{' '}
              <span className="font-semibold">{total}</span> conversations
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 border border-slate-300 dark:border-slate-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 border border-slate-300 dark:border-slate-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* View Conversation Details Modal */}
      {viewingConversation && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setViewingConversation(null)}
        >
          <div 
            className="bg-white dark:bg-slate-800 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700 animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-red-50 to-orange-50 dark:from-slate-800 dark:to-slate-800">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-2xl font-semibold text-red-600 dark:text-white flex items-center gap-2">
                    <span className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                      <AlertTriangle className="text-red-600 dark:text-red-400" size={25} /></span>
                    Flagged Conversation Details
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    <span className="font-medium">User:</span> {viewingConversation.user_email} | 
                    <span className="font-medium ml-2">Conversation:</span> {viewingConversation.title || 'Untitled'}
                  </p>
                </div>
                <button
                  onClick={() => setShowEmailMessage(true)}
                  className="px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium text-sm flex items-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                  Help User via Email
                </button>
              </div>
            </div>
            
            {showEmailMessage && (
              <div className="px-6 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800 animate-in slide-in-from-top duration-300">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M2 12h20"/></svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Email Service Not Configured</p>
                      <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">The email service is not yet set up. Please configure SMTP settings to contact users directly.</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowEmailMessage(false)}
                    className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>
            )}
            
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                {/* Stats Indicators */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
                    <div className="flex items-center gap-2 mb-2">
                      <Eye className="text-orange-600 dark:text-orange-400" size={18} />
                      <p className="text-sm font-medium text-orange-900 dark:text-orange-100">Pending Review</p>
                    </div>
                    <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {viewingConversation.flagged_messages?.filter(m => !m.reviewed).length || 0}
                    </p>
                  </div>
                  
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="text-green-600 dark:text-green-400" size={18} />
                      <p className="text-sm font-medium text-green-900 dark:text-green-100">Reviewed</p>
                    </div>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {viewingConversation.flagged_messages?.filter(m => m.reviewed).length || 0}
                    </p>
                  </div>
                </div>
                
                {/* Display all flagged messages */}
                {viewingConversation.flagged_messages?.map((msg, index) => (
                  <div key={msg.message_id} className="border-2 border-red-200 dark:border-blue-950 rounded-lg p-5 bg-white dark:bg-slate-900">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-1.5">
                          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-pink-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                            {index + 1}
                          </div>
                          {msg.reviewed ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
                              <CheckCircle size={10} />
                              Reviewed
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300">
                              <Eye size={10} />
                              Needs Review
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 ml-5">
                          <Clock size={10} />
                          {msg.created_at ? format(new Date(msg.created_at), 'MMM d, yyyy HH:mm:ss') : 'N/A'}
                        </p>
                      </div>
                    </div>

                    <div className="mb-5">
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2 ml-1">Message Content:</p>
                      <div className="p-5 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                        <p className="text-base text-slate-800 dark:text-slate-300 whitespace-pre-wrap break-words">
                          {msg.content}
                        </p>
                      </div>
                    </div>

                    {msg.metadata?.moderation?.matched_keywords && msg.metadata.moderation.matched_keywords.length > 0 && (
                      <div className="mb-2">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                            🚨 Flagged Keywords :
                          </p>
                          {msg.metadata?.moderation?.severity && (
                             <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                              Severity : <span className="text-red-600 dark:text-red-400 font-semibold capitalize">{msg.metadata.moderation.severity}</span>
                              </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-2 mb-4">
                          {msg.metadata.moderation.matched_keywords.map((keyword, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-300 dark:border-red-800/80 rounded text-xs font-medium ml-7"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {!msg.reviewed && (
                      <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                        <button
                          onClick={() => handleResolveMessage(msg.message_id)}
                          disabled={resolvingMessages.has(msg.message_id)}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {resolvingMessages.has(msg.message_id) ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              Resolving...
                            </>
                          ) : (
                            <>
                              <CheckCircle size={16} />
                              Mark as Reviewed
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="px-6 py-4 bg-slate-50 dark:bg-slate-900 rounded-b-xl flex justify-between items-center border-t border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setViewingConversation(null)}
                className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300 font-medium"
              >
                <X size={16} className="inline mr-2" />
                Close
              </button>
              
              <button
                onClick={handleMarkAllReviewed}
                disabled={!viewingConversation.flagged_messages?.some(m => !m.reviewed) || resolvingMessages.size > 0}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resolvingMessages.size > 0 ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Marking All...
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} />
                    Mark All Reviewed
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
