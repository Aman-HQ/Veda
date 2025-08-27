// Mock WebSocket hook for token streaming during Phase F
// Interface:
// - connect(token, conversationId)
// - onChunk(cb)      // cb(textChunk)
// - onDone(cb)       // cb(finalText)
// - onError(cb)      // cb(error)
// - disconnect()

let intervalId = null;
let connectedConversationId = null;
let isStreaming = false;
const chunkListeners = new Set();
const doneListeners = new Set();
const errorListeners = new Set();

const STATIC_TEXT = 'This is a streamed mock response for testing.';

function emitChunk(text) {
  chunkListeners.forEach((cb) => {
    try { cb(text); } catch (e) { /* noop */ }
  });
}

function emitDone(finalText) {
  doneListeners.forEach((cb) => {
    try { cb(finalText); } catch (e) { /* noop */ }
  });
}

function emitError(err) {
  errorListeners.forEach((cb) => {
    try { cb(err); } catch (e) { /* noop */ }
  });
}

export default function useWebSocket() {
  function connect(token, conversationId) {
    // Guard: prevent duplicate intervals for the same conversation
    if (isStreaming && connectedConversationId === conversationId) {
      return; // already streaming for this conversation, resume safely
    }

    disconnect(); // clear any prior stream before starting a new one

    connectedConversationId = conversationId || 'unknown';
    const words = STATIC_TEXT.split(' ');
    let idx = 0;
    isStreaming = true;

    intervalId = setInterval(() => {
      if (!isStreaming) return;
      if (idx < words.length) {
        const next = (idx === 0 ? '' : ' ') + words[idx];
        emitChunk(next);
        idx += 1;
      } else {
        clearInterval(intervalId);
        intervalId = null;
        isStreaming = false;
        emitDone(STATIC_TEXT);
      }
    }, Math.floor(50 + Math.random() * 30));
  }

  function onChunk(cb) {
    if (typeof cb === 'function') chunkListeners.add(cb);
    return () => chunkListeners.delete(cb);
  }

  function onDone(cb) {
    if (typeof cb === 'function') doneListeners.add(cb);
    return () => doneListeners.delete(cb);
  }

  function onError(cb) {
    if (typeof cb === 'function') errorListeners.add(cb);
    return () => errorListeners.delete(cb);
  }

  function disconnect() {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
    isStreaming = false;
    // do not clear listeners here; caller manages subscriptions via returned unsubscribe
  }

  return { connect, onChunk, onDone, onError, disconnect };
}


