import { useMemo, useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import uiStore from '../../stores/uiStore.js';

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
  const [openMenuId, setOpenMenuId] = useState(null);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const buttonRefs = useRef({});

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
    const trimmedTitle = editTitle.trim();
    if (trimmedTitle && trimmedTitle !== '') {
      try {
        await onRename?.(id, trimmedTitle);
        setEditingId(null);
        setEditTitle('');
      } catch (error) {
        console.error('Failed to rename conversation:', error);
      }
    } else {
      setEditingId(null);
      setEditTitle('');
    }
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const toggleMenu = (e, conversationId) => {
    e.stopPropagation();
    if (openMenuId === conversationId) {
      setOpenMenuId(null);
    } else {
      // Calculate position for the dropdown
      const button = buttonRefs.current[conversationId];
      if (button) {
        const rect = button.getBoundingClientRect();
        setMenuPosition({
          top: rect.top,
          left: rect.right + 8 // 8px gap from button
        });
      }
      setOpenMenuId(conversationId);
    }
  };

  // Close menu when clicking outside
  const handleClickOutside = () => {
    if (openMenuId) setOpenMenuId(null);
  };

  useEffect(() => {
    if (openMenuId) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [openMenuId]);

  return (
    <div className="flex flex-col flex-1 min-h-0" aria-label="Conversations">
      {/* New Chat Button */}
      <div 
        className="flex-shrink-0 p-3 border-b transition-colors duration-300"
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

      {/* Search Button/Bar */}
      {!isSearchOpen ? (
        <div 
          className="flex-shrink-0 p-3 border-b transition-colors duration-300"
          style={{ borderColor: 'var(--sidebar-border)' }}
        >
          <button
            onClick={() => setIsSearchOpen(true)}
            className="w-full flex items-center gap-2 px-4 py-2 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--sidebar-border)',
              color: 'var(--sidebar-text-secondary)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
              e.currentTarget.style.color = 'var(--sidebar-text)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
            }}
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <span className="text-sm">Search conversations</span>
          </button>
        </div>
      ) : (
        <div 
          className="flex-shrink-0 relative p-3 border-b transition-colors duration-300"
          style={{ borderColor: 'var(--sidebar-border)' }}
        >
          {/* Search Icon */}
          <div className="absolute left-6 top-1/2 transform -translate-y-1/2 pointer-events-none">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              style={{ color: 'var(--sidebar-text-secondary)' }}
            >
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
          </div>

          {/* Search Input */}
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-9 py-2 rounded-lg text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid var(--sidebar-border)',
              color: 'var(--sidebar-text)',
              fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }}
            onFocus={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
            }}
            onBlur={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
              e.currentTarget.style.borderColor = 'var(--sidebar-border)';
            }}
            autoFocus
          />

          {/* Close Button */}
          <button
            onClick={() => {
              setSearchQuery('');
              setIsSearchOpen(false);
            }}
            className="absolute right-6 top-1/2 transform -translate-y-1/2 inline-flex items-center justify-center h-6 w-6 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
            style={{ color: 'var(--sidebar-text-secondary)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
              e.currentTarget.style.color = 'var(--sidebar-text)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
            }}
            aria-label="Close search"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      )}

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto overflow-x-visible">
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
                  if (actions && openMenuId !== c.id) actions.style.opacity = '1';
                }}
                onMouseLeave={(e) => {
                  const actions = e.currentTarget.querySelector('.conversation-actions');
                  // Keep visible if conversation is pinned or menu is open
                  if (actions && openMenuId !== c.id && !c.isPinned) actions.style.opacity = '0';
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
                      {/* Title */}
                      <div className="truncate font-medium leading-relaxed flex-1" style={{ fontSize: '14.5px', lineHeight: '1.5' }}>
                        {c.title || 'Untitled conversation'}
                      </div>
                    </div>
                  </button>
                )}

                {/* Action Buttons (Pin icon + 3-dots menu) */}
                {editingId !== c.id && (
                  <div 
                    className="conversation-actions absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1"
                    style={{ opacity: (openMenuId === c.id || c.isPinned) ? 1 : 0 }}
                  >
                    {/* Pin/Unpin Icon Button - Always visible when conversation is pinned OR on hover */}
                    {c.isPinned && (
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          await onPin?.(c.id, false); // Unpin
                        }}
                        className="inline-flex items-center justify-center h-7 w-7 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                        style={{ 
                          color: 'var(--accent-primary)',
                          backgroundColor: 'var(--sidebar-bg)'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'var(--sidebar-bg)';
                        }}
                        title="Unpin conversation"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M16 12V4H17V2H7V4H8V12L6 14V16H11.2V22H12.8V16H18V14L16 12Z" />
                        </svg>
                      </button>
                    )}

                    {/* 3-Dots Button */}
                    <button
                      ref={(el) => buttonRefs.current[c.id] = el}
                      onClick={(e) => toggleMenu(e, c.id)}
                      className="inline-flex items-center justify-center h-7 w-7 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                      style={{ 
                        color: 'var(--sidebar-text-secondary)',
                        backgroundColor: openMenuId === c.id ? 'var(--sidebar-hover)' : 'var(--sidebar-bg)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                        e.currentTarget.style.color = 'var(--sidebar-text)';
                      }}
                      onMouseLeave={(e) => {
                        if (openMenuId !== c.id) {
                          e.currentTarget.style.backgroundColor = 'var(--sidebar-bg)';
                          e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
                        }
                      }}
                      title="More options"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="1"></circle>
                        <circle cx="12" cy="5" r="1"></circle>
                        <circle cx="12" cy="19" r="1"></circle>
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </nav>
      </div>

      {/* Dropdown Menu Portal - Rendered outside sidebar */}
      {openMenuId && createPortal(
        <div 
          className="fixed w-44 rounded-lg shadow-xl border z-[9999]"
          style={{
            top: `${menuPosition.top}px`,
            left: `${menuPosition.left}px`,
            backgroundColor: 'var(--sidebar-bg)',
            borderColor: 'var(--sidebar-border)',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {sortedConversations.map((c) => 
            c.id === openMenuId ? (
              <div key={c.id}>
                {/* Pin/Unpin */}
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    await onPin?.(c.id, !c.isPinned);
                    setOpenMenuId(null);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm outline-none transition-all rounded-t-lg"
                  style={{ color: 'var(--sidebar-text)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={c.isPinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 12V4H17V2H7V4H8V12L6 14V16H11.2V22H12.8V16H18V14L16 12Z" />
                  </svg>
                  {c.isPinned ? 'Unpin' : 'Pin'}
                </button>

                {/* Rename */}
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    setOpenMenuId(null);
                    handleRename(c.id, c.title);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm outline-none transition-all"
                  style={{ color: 'var(--sidebar-text)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
                  </svg>
                  Rename
                </button>

                {/* Delete */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete this conversation?')) {
                      onDelete?.(c.id);
                    }
                    setOpenMenuId(null);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm outline-none rounded-b-lg transition-all"
                  style={{ color: '#ef4444' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                  Delete
                </button>
              </div>
            ) : null
          )}
        </div>,
        document.body
      )}
    </div>
  );
}

