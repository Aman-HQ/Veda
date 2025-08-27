import { useMemo } from 'react';
import uiStore from '../../stores/uiStore.js';

export default function ConversationList({
  conversations = [],
  activeId = null,
  onSelect,
  onNewConversation,
}) {
  const items = useMemo(() => conversations, [conversations]);

  return (
    <div className="flex h-full flex-col" aria-label="Conversations">
      <div className="p-2 border-b border-slate-200 dark:border-slate-800">
        <button
          className="w-full text-left px-3 py-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900"
          onClick={onNewConversation}
          aria-label="Start a new chat"
        >
          New chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <nav className="p-2 space-y-1" role="list">
          {items.length === 0 ? (
            <div className="text-sm text-slate-500 dark:text-slate-400 px-2 py-2">No conversations</div>
          ) : (
            items.map((c) => (
              <button
                key={c.id}
                onClick={() => {
                  uiStore.setActiveConversation(c.id);
                  onSelect?.(c.id);
                }}
                className={`w-full text-left px-3 py-2 rounded-md hover:bg-slate-50 dark:hover:bg-slate-800 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 transition-colors ${
                  c.id === activeId
                    ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                    : 'text-slate-700 dark:text-slate-200'
                }`}
                aria-current={c.id === activeId ? 'page' : undefined}
                aria-label={`Open conversation ${c.title || 'Untitled conversation'}`}
                role="listitem"
              >
                <div className="truncate font-medium">{c.title || 'Untitled conversation'}</div>
                {c.lastMessage ? (
                  <div className="truncate text-xs text-slate-500 dark:text-slate-400">{c.lastMessage}</div>
                ) : null}
              </button>
            ))
          )}
        </nav>
      </div>
    </div>
  );
}

