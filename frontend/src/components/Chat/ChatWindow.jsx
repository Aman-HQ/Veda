import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble.jsx';
import TypingIndicator from './TypingIndicator.jsx';
import { listMessages, createMessage } from '../../services/chatService.js';
import useWebSocket from '../../hooks/useWebSocket.js';

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

  // Start mock streaming when the latest message is from user and no assistant follows
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

    unsubChunk = ws.onChunk((chunk) => {
      setDraftAssistant((prev) => prev + chunk);
    });
    unsubDone = ws.onDone(async (finalText) => {
      try {
        await createMessage({ conversationId, role: 'assistant', content: finalText });
        setDraftAssistant('');
        setStreaming(false);
        onAssistantDone?.();
      } catch (e) {
        setError('Failed to finalize message.');
        setStreaming(false);
      } finally {
        ws.disconnect();
        unsubChunk?.();
        unsubDone?.();
        unsubError?.();
      }
    });
    unsubError = ws.onError((err) => {
      setError('Streaming error.');
      setStreaming(false);
      ws.disconnect();
      unsubChunk?.();
      unsubDone?.();
      unsubError?.();
    });

    ws.connect('mock-access-token', conversationId);

    return () => {
      ws.disconnect();
      unsubChunk?.();
      unsubDone?.();
      unsubError?.();
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


