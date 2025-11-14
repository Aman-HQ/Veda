// Real WebSocket hook for streaming chat responses
// Interface:
// - connect(token, conversationId)
// - onChunk(cb)      // cb(textChunk)
// - onDone(cb)       // cb(finalText)
// - onError(cb)      // cb(error)
// - sendMessage(message)
// - disconnect()

const WS_URL = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';

let ws = null;
let connectedConversationId = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 2000;

const chunkListeners = new Set();
const doneListeners = new Set();
const errorListeners = new Set();
const messageListeners = new Set();

function emitChunk(messageId, text) {
  chunkListeners.forEach((cb) => {
    try { cb(messageId, text); } catch (e) { console.error('Chunk listener error:', e); }
  });
}

function emitDone(messageId, fullText) {
  doneListeners.forEach((cb) => {
    try { cb(messageId, fullText); } catch (e) { console.error('Done listener error:', e); }
  });
}

function emitError(err) {
  errorListeners.forEach((cb) => {
    try { cb(err); } catch (e) { console.error('Error listener error:', e); }
  });
}

function emitMessage(data) {
  messageListeners.forEach((cb) => {
    try { cb(data); } catch (e) { console.error('Message listener error:', e); }
  });
}

export default function useWebSocket() {
  function connect(token, conversationId) {
    return new Promise((resolve, reject) => {
      if (ws && ws.readyState === WebSocket.OPEN && connectedConversationId === conversationId) {
        console.log('WebSocket already connected to this conversation');
        resolve();
        return;
      }

      disconnect(); // Clean up any existing connection

      connectedConversationId = conversationId;
      const wsUrl = `${WS_URL}/ws/conversations/${conversationId}?token=${encodeURIComponent(token)}`;

      console.log('Connecting to WebSocket:', wsUrl);
      console.log('Token type:', token.startsWith('eyJ') ? 'JWT' : 'Unknown', 'Length:', token.length);

      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('WebSocket connected successfully');
          reconnectAttempts = 0;
          resolve();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data.type);

            switch (data.type) {
              case 'chunk':
                emitChunk(data.messageId, data.text);
                break;
              case 'done':
                emitDone(data.messageId, data.fullText);
                break;
              case 'error':
                emitError(data.message || 'Unknown error');
                break;
              case 'user_message_saved':
              case 'blocked':
                emitMessage(data);
                break;
              default:
                console.log('Unknown message type:', data.type, data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
            emitError('Failed to parse server message');
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          emitError('WebSocket connection error');
          reject(error);
        };

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          
          // Attempt reconnection for unexpected closures
          if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
            
            setTimeout(() => {
              if (connectedConversationId && token) {
                connect(token, connectedConversationId);
              }
            }, RECONNECT_DELAY * reconnectAttempts);
          }
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        emitError('Failed to establish WebSocket connection');
        reject(error);
      }
    });
  }

  function sendMessage(message) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      emitError('Not connected to server');
      return false;
    }

    try {
      ws.send(JSON.stringify(message));
      console.log('Message sent:', message.type);
      return true;
    } catch (error) {
      console.error('Error sending message:', error);
      emitError('Failed to send message');
      return false;
    }
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

  function onMessage(cb) {
    if (typeof cb === 'function') messageListeners.add(cb);
    return () => messageListeners.delete(cb);
  }

  function disconnect() {
    if (ws) {
      console.log('Disconnecting WebSocket...');
      reconnectAttempts = MAX_RECONNECT_ATTEMPTS; // Prevent reconnection
      ws.close(1000, 'Client disconnect');
      ws = null;
    }
    connectedConversationId = null;
  }

  return { connect, sendMessage, onChunk, onDone, onError, onMessage, disconnect };
}


