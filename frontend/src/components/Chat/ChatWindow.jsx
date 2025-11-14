import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble.jsx';
import TypingIndicator from './TypingIndicator.jsx';
import { listMessages, createMessage } from '../../services/chatService.js';
import useWebSocket from '../../hooks/useWebSocket.js';
import authStore from '../../stores/authStore.js';

export default function ChatWindow({ conversationId, reloadToken, onAssistantDone }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [draftAssistant, setDraftAssistant] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState('');
  const scrollRef = useRef(null);
  const bottomAnchorRef = useRef(null);
  const lastConversationIdRef = useRef(null);
  const ws = useWebSocket();

  useEffect(() => {
    let isCancelled = false;
    const isSwitch = conversationId !== lastConversationIdRef.current;
    async function load() {
      if (!conversationId) {
        setMessages([]);
        setLoading(false);
        lastConversationIdRef.current = null;
        return;
      }
      if (isSwitch) setLoading(true);
      try {
        const list = await listMessages(conversationId);
        if (!isCancelled) setMessages(list);
      } finally {
        if (!isCancelled && isSwitch) setLoading(false);
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
    // smooth scroll only when not first load
    el.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, streaming, draftAssistant]);

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
        <div className="max-w-2xl mx-auto w-full py-6 sm:py-8 space-y-4">
          {!conversationId ? (
            <div className="text-center text-slate-500 dark:text-slate-400 text-sm">
              Start typing below to begin a new conversation.
            </div>
          ) : loading ? (
            <div className="text-center text-slate-500 dark:text-slate-400 text-sm">Loading…</div>
          ) : messages.length === 0 ? (
            <div className="text-center text-slate-500 dark:text-slate-400 text-sm">
              Start a conversation by sending a message.
            </div>
          ) : (
            messages.map((m) => (
              <MessageBubble key={m.id} role={m.role} createdAt={m.createdAt}>
                {m.content}
              </MessageBubble>
            ))
          )}
          {streaming ? <TypingIndicator /> : null}
          {draftAssistant ? (
            <MessageBubble role="assistant">{draftAssistant}</MessageBubble>
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


