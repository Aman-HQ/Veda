
import { useEffect, useMemo, useState } from 'react';
import ChatWindow from '../components/Chat/ChatWindow.jsx';
import Composer from '../components/Chat/Composer.jsx';
import ConversationList from '../components/Chat/ConversationList.jsx';
import ChatLayout from '../components/Chat/ChatLayout.jsx';
import { createConversation, listConversations, deleteConversation, updateConversation } from '../services/chatService.js';
import uiStore from '../stores/uiStore.js';
import useWebSocket from '../hooks/useWebSocket.js';
import authStore from '../stores/authStore.js';


export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(uiStore.getState().activeConversationId);
  const [reloadToken, setReloadToken] = useState(0); // triggers message list refresh without remounting
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const ws = useWebSocket();

  // Set up WebSocket message listener for user_message_saved events
  useEffect(() => {
    const unsubMessage = ws.onMessage((data) => {
      if (data.type === 'user_message_saved') {
        console.log('User message saved, refreshing UI');
        setReloadToken((n) => n + 1);
      }
    });

    return () => {
      unsubMessage?.();
    };
  }, [ws]);

  useEffect(() => {
    async function load() {
      const list = await listConversations();
      setConversations(list);
      if (list.length && !uiStore.getState().activeConversationId) {
        uiStore.setActiveConversation(list[0].id);
        setActiveConversationId(list[0].id);
      }
    }
    load();
    const unsub = uiStore.subscribe((s) => setActiveConversationId(s.activeConversationId));
    return () => unsub?.();
  }, []);

  const handleRename = async (id, newTitle) => {
    try {
      await updateConversation(id, { title: newTitle });
      const list = await listConversations();
      setConversations(list);
    } catch (error) {
      console.error('Failed to rename conversation:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteConversation(id);
      const list = await listConversations();
      setConversations(list);
      
      // If deleted conversation was active, clear active conversation
      if (id === activeConversationId) {
        setActiveConversationId(null);
        uiStore.setActiveConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handlePin = async (id, isPinned) => {
    try {
      await updateConversation(id, { isPinned });
      const list = await listConversations();
      setConversations(list);
    } catch (error) {
      console.error('Failed to pin conversation:', error);
    }
  };

  const sidebar = useMemo(() => (
    <ConversationList
      conversations={conversations}
      activeId={activeConversationId}
      onSelect={setActiveConversationId}
      onNewConversation={async () => {
        const created = await createConversation({ title: 'New conversation' });
        const list = await listConversations();
        setConversations(list);
        setActiveConversationId(created.id);
      }}
      onRename={handleRename}
      onDelete={handleDelete}
      onPin={handlePin}
    />
  ), [conversations, activeConversationId]);

  const handleSend = async (text) => {
    let conversationId = activeConversationId;
    
    // Clear selected prompt after sending
    setSelectedPrompt('');
    
    // If no active conversation, create one automatically
    if (!conversationId) {
      try {
        const created = await createConversation({ title: 'New conversation' });
        conversationId = created.id;
        
        // Update conversations list and set as active
        const list = await listConversations();
        setConversations(list);
        setActiveConversationId(conversationId);
        uiStore.setActiveConversation(conversationId);
      } catch (error) {
        console.error('Failed to create conversation:', error);
        return;
      }
    }
    
    // Send message through WebSocket for moderation and streaming
    const accessToken = authStore.getAccessToken();
    if (!accessToken) {
      console.error('No access token available');
      return;
    }

    try {
      // Connect WebSocket and wait for connection to establish
      await ws.connect(accessToken, conversationId);
      
      // Send message with unique client ID
      const clientMessageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const sent = ws.sendMessage({
        type: 'message',
        text: text,
        client_message_id: clientMessageId
      });
      
      if (!sent) {
        console.error('Failed to send message - WebSocket not connected');
        return;
      }

      // Don't manually trigger refresh - wait for user_message_saved event
      console.log('Message sent, waiting for server confirmation...');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <ChatLayout sidebarContent={sidebar}>
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto">
          <ChatWindow
            conversationId={activeConversationId}
            reloadToken={reloadToken}
            onAssistantDone={() => setReloadToken((n) => n + 1)}
            onPromptSelected={setSelectedPrompt}
          />
        </div>
        <div className='mt-2'>
          <Composer
            onSend={handleSend}
            initialValue={selectedPrompt}
            onAttachImage={(file) => {
              console.log('Selected image (mock):', file?.name);
            }}
            onStartVoice={() => {
              setTimeout(async () => {
                const fakeTranscript = 'This is a mock voice transcription.';
                await handleSend(fakeTranscript);
              }, 800);
            }}
            onStopVoice={() => {
              // no-op placeholder
            }}
          />
        </div>
      </div>
    </ChatLayout>
  );
}

