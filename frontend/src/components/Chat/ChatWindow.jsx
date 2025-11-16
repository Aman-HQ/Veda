import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble.jsx';
import TypingIndicator from './TypingIndicator.jsx';
import EmptyState from './EmptyState.jsx';
import { listMessages, createMessage } from '../../services/chatService.js';
import useWebSocket from '../../hooks/useWebSocket.js';
import authStore from '../../stores/authStore.js';

export default function ChatWindow({ conversationId, reloadToken, onAssistantDone, onPromptSelected, onEditMessage }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [draftAssistant, setDraftAssistant] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState('');
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const scrollRef = useRef(null);
  const bottomAnchorRef = useRef(null);
  const lastConversationIdRef = useRef(null);
  const ws = useWebSocket();

  const user = authStore.getUser();
  const username = user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'there';

  const handlePromptClick = (prompt) => {
    onPromptSelected?.(prompt);
  };

  useEffect(() => {
    let isCancelled = false;
    const isSwitch = conversationId !== lastConversationIdRef.current;
    
    async function load() {
      if (!conversationId) {
        setMessages([]);
        setLoading(false);
        setIsInitialLoad(true);
        lastConversationIdRef.current = null;
        return;
      }
      if (isSwitch) {
        setLoading(true);
        setIsInitialLoad(true); // Mark as initial load for conversation switch
      }
      try {
        const list = await listMessages(conversationId);
        if (!isCancelled) setMessages(list);
      } finally {
        if (!isCancelled && isSwitch) {
          setLoading(false);
          // Set isInitialLoad to false after a short delay to allow instant scroll
          setTimeout(() => setIsInitialLoad(false), 100);
        }
        lastConversationIdRef.current = conversationId;
      }
    }
    load();
    return () => {
      isCancelled = true;
    };
  }, [conversationId, reloadToken]);

  useEffect(() => {
    // Auto-scroll to bottom when messages change or typing state toggles
    const el = bottomAnchorRef.current;
    if (!el) return;
    
    // Use instant scroll for initial loads and conversation switches to avoid animation
    // Use smooth scroll only for new messages in the same conversation
    const behavior = isInitialLoad ? 'instant' : 'smooth';
    el.scrollIntoView({ behavior, block: 'end' });
  }, [messages, streaming, draftAssistant, isInitialLoad]);

  // Start streaming when the latest message is from user and no assistant follows
  useEffect(() => {
    if (!conversationId) return;
    if (streaming) return;
    if (!messages.length) return;
    const last = messages[messages.length - 1];
    if (last.role !== 'user') return;

    // Begin streaming
    setError('');
    setDraftAssistant('');
    setStreaming(true);

    let unsubChunk = () => {};
    let unsubDone = () => {};
    let unsubError = () => {};
    let unsubMessage = () => {};

    unsubChunk = ws.onChunk((messageId, chunk) => {
      setDraftAssistant((prev) => prev + chunk);
    });
    
    unsubDone = ws.onDone(async (messageId, finalText) => {
      try {
        // No need to create message - backend already saved it
        setDraftAssistant('');
        setStreaming(false);
        onAssistantDone?.();
      } catch (e) {
        setError('Failed to finalize message.');
        setStreaming(false);
      } finally {
        unsubChunk?.();
        unsubDone?.();
        unsubError?.();
        unsubMessage?.();
      }
    });
    
    unsubError = ws.onError((err) => {
      setError(typeof err === 'string' ? err : 'Streaming error.');
      setStreaming(false);
      unsubChunk?.();
      unsubDone?.();
      unsubError?.();
      unsubMessage?.();
    });

    // Handle special message events (blocked, flagged, etc.)
    unsubMessage = ws.onMessage((data) => {
      if (data.type === 'blocked') {
        setError('Message blocked due to safety concerns.');
        setStreaming(false);
        setDraftAssistant(data.safe_response || 'Your message could not be sent.');
        onAssistantDone?.(); // Refresh to show blocked message
        unsubChunk?.();
        unsubDone?.();
        unsubError?.();
        unsubMessage?.();
      } else if (data.type === 'user_message_saved') {
        // User message was saved, trigger refresh
        onAssistantDone?.();
      }
    });

    const accessToken = authStore.getAccessToken();
    if (!accessToken) {
      setError('Authentication required');
      setStreaming(false);
      return;
    }

    ws.connect(accessToken, conversationId);

    return () => {
      unsubChunk?.();
      unsubDone?.();
      unsubError?.();
      unsubMessage?.();
    };
  }, [conversationId, messages, streaming]);

  return (
    <div className="flex-1 min-h-0" role="main" aria-label="Chat conversation">
      <div ref={scrollRef} className="h-full overflow-y-auto px-4 sm:px-6">
        <div className="max-w-3xl mx-auto w-full py-6 sm:py-8 space-y-8">
          {!conversationId ? (
            <EmptyState username={username} onPromptClick={handlePromptClick} />
          ) : loading ? (
            <div className="text-center text-slate-500 dark:text-slate-400 text-sm">Loading…</div>
          ) : messages.length === 0 ? (
            <EmptyState username={username} onPromptClick={handlePromptClick} />
          ) : (
            messages.map((m) => (
              <div key={m.id} className="group">
                <MessageBubble role={m.role} createdAt={m.createdAt} messageId={m.id} onEditMessage={onEditMessage}>
                  {m.content}
                </MessageBubble>
              </div>
            ))
          )}
          {streaming ? <TypingIndicator /> : null}
          {draftAssistant ? (
            <div className="group">
              <MessageBubble role="assistant">{draftAssistant}</MessageBubble>
            </div>
          ) : null}
          {error ? (
            <div className="text-center text-xs text-red-500">{error}</div>
          ) : null}
          <div ref={bottomAnchorRef} />
        </div>
      </div>
    </div>
  );
}


