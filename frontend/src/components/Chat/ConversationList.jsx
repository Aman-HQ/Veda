import { useMemo, useState } from 'react';
import uiStore from '../../stores/uiStore.js';
import ConversationSearch from './ConversationSearch.jsx';

export default function ConversationList({
  conversations = [],
  activeId = null,
  onSelect,
  onNewConversation,
  onRename,
  onDelete,
  onPin,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const filteredConversations = useMemo(() => {
    if (!searchQuery) return conversations;
    const query = searchQuery.toLowerCase();
    return conversations.filter(c => 
      (c.title || '').toLowerCase().includes(query)
    );
  }, [conversations, searchQuery]);

  // Sort: pinned first, then by date
  const sortedConversations = useMemo(() => {
    return [...filteredConversations].sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return 0;
    });
  }, [filteredConversations]);

  const handleRename = (id, currentTitle) => {
    setEditingId(id);
    setEditTitle(currentTitle || 'Untitled conversation');
  };

  const handleSaveRename = async (id) => {
    if (editTitle.trim()) {
      await onRename?.(id, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditTitle('');
  };

  return (
    <div className="flex h-full flex-col" aria-label="Conversations">
      {/* New Chat Button */}
      <div 
        className="p-3 border-b transition-colors duration-300"
        style={{ borderColor: 'var(--sidebar-border)' }}
      >
        <button
          className="w-full text-left px-4 py-2.5 rounded-lg border text-white font-medium shadow-lg outline-none focus-visible:ring-2 transition-all"
          style={{
            background: 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-primary-hover) 100%)',
            borderColor: 'transparent',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.boxShadow = '0 8px 16px rgba(59, 130, 246, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
          }}
          onClick={onNewConversation}
          aria-label="Start a new chat"
        >
          + New Chat
        </button>
      </div>

      {/* Search */}
      <ConversationSearch onSearch={setSearchQuery} />

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        <nav className="p-2 space-y-1" role="list">
          {sortedConversations.length === 0 ? (
            <div 
              className="text-sm px-3 py-2 transition-colors duration-300"
              style={{ color: 'var(--sidebar-text-secondary)' }}
            >
              {searchQuery ? 'No conversations found' : 'No conversations'}
            </div>
          ) : (
            sortedConversations.map((c) => (
              <div
                key={c.id}
                className="group relative"
                onMouseEnter={(e) => {
                  const actions = e.currentTarget.querySelector('.conversation-actions');
                  if (actions) actions.style.opacity = '1';
                }}
                onMouseLeave={(e) => {
                  const actions = e.currentTarget.querySelector('.conversation-actions');
                  if (actions) actions.style.opacity = '0';
                }}
              >
                {editingId === c.id ? (
                  /* Edit Mode */
                  <div className="px-2 py-2">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveRename(c.id);
                        if (e.key === 'Escape') handleCancelRename();
                      }}
                      className="w-full px-3 py-2 rounded-lg text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                      style={{
                        backgroundColor: 'var(--sidebar-hover)',
                        color: 'var(--sidebar-text)',
                        border: '1px solid var(--sidebar-border)'
                      }}
                      autoFocus
                    />
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleSaveRename(c.id)}
                        className="flex-1 px-2 py-1 rounded text-xs font-medium"
                        style={{
                          backgroundColor: 'var(--accent-primary)',
                          color: 'white'
                        }}
                      >
                        Save
                      </button>
                      <button
                        onClick={handleCancelRename}
                        className="flex-1 px-2 py-1 rounded text-xs font-medium"
                        style={{
                          backgroundColor: 'var(--sidebar-hover)',
                          color: 'var(--sidebar-text)'
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Normal Mode */
                  <button
                    onClick={() => {
                      uiStore.setActiveConversation(c.id);
                      onSelect?.(c.id);
                    }}
                    className={`w-full text-left px-4 py-3 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all ${
                      c.id === activeId ? 'bg-slate-700/70' : ''
                    }`}
                    style={{
                      color: c.id === activeId ? 'var(--sidebar-text)' : 'var(--sidebar-text-secondary)',
                      backgroundColor: c.id === activeId ? 'var(--sidebar-hover)' : 'transparent'
                    }}
                    onMouseEnter={(e) => {
                      if (c.id !== activeId) {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                        e.currentTarget.style.color = 'var(--sidebar-text)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (c.id !== activeId) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
                      }
                    }}
                    aria-current={c.id === activeId ? 'page' : undefined}
                    aria-label={`Open conversation ${c.title || 'Untitled conversation'}`}
                    role="listitem"
                  >
                    <div className="flex items-center gap-2">
                      {/* Pin Icon */}
                      {c.isPinned && (
                        <svg 
                          xmlns="http://www.w3.org/2000/svg" 
                          width="14" 
                          height="14" 
                          viewBox="0 0 24 24" 
                          fill="currentColor" 
                          stroke="none"
                          style={{ color: 'var(--accent-primary)' }}
                        >
                          <path d="M16 12V4H17V2H7V4H8V12L6 14V16H11.2V22H12.8V16H18V14L16 12Z" />
                        </svg>
                      )}
                      
                      {/* Title */}
                      <div className="truncate font-medium leading-relaxed flex-1" style={{ fontSize: '14.5px', lineHeight: '1.5' }}>
                        {c.title || 'Untitled conversation'}
                      </div>
                    </div>
                  </button>
                )}

                {/* Action Buttons (shown on hover) */}
                {editingId !== c.id && (
                  <div 
                    className="conversation-actions absolute right-2 top-1/2 transform -translate-y-1/2 flex gap-1 transition-opacity duration-200"
                    style={{ opacity: 0 }}
                  >
                    {/* Pin/Unpin */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onPin?.(c.id, !c.isPinned);
                      }}
                      className="inline-flex items-center justify-center h-7 w-7 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                      style={{ 
                        color: c.isPinned ? 'var(--accent-primary)' : 'var(--sidebar-text-secondary)',
                        backgroundColor: 'var(--sidebar-bg)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                        e.currentTarget.style.color = 'var(--accent-primary)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-bg)';
                        e.currentTarget.style.color = c.isPinned ? 'var(--accent-primary)' : 'var(--sidebar-text-secondary)';
                      }}
                      title={c.isPinned ? 'Unpin' : 'Pin'}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={c.isPinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M16 12V4H17V2H7V4H8V12L6 14V16H11.2V22H12.8V16H18V14L16 12Z" />
                      </svg>
                    </button>

                    {/* Rename */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRename(c.id, c.title);
                      }}
                      className="inline-flex items-center justify-center h-7 w-7 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                      style={{ 
                        color: 'var(--sidebar-text-secondary)',
                        backgroundColor: 'var(--sidebar-bg)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                        e.currentTarget.style.color = 'var(--sidebar-text)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-bg)';
                        e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
                      }}
                      title="Rename"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
                      </svg>
                    </button>

                    {/* Delete */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('Delete this conversation?')) {
                          onDelete?.(c.id);
                        }
                      }}
                      className="inline-flex items-center justify-center h-7 w-7 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                      style={{ 
                        color: 'var(--sidebar-text-secondary)',
                        backgroundColor: 'var(--sidebar-bg)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                        e.currentTarget.style.color = '#ef4444';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-bg)';
                        e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
                      }}
                      title="Delete"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </nav>
      </div>
    </div>
  );
}

