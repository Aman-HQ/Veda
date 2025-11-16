import * as mockApi from './mockApi.js';
import api from './api.js';

// Default to mock API during Phase F. If the env var is absent, treat as 'true'.
const useMock = (import.meta.env.VITE_USE_MOCK_API ?? 'true') === 'true';

const realApi = {
  async listConversations() {
    try {
      const response = await api.get('/api/conversations');
      // Map snake_case to camelCase
      return response.data.map(conv => ({
        ...conv,
        isPinned: conv.is_pinned ?? false,
        messagesCount: conv.messages_count,
        userId: conv.user_id,
        createdAt: conv.created_at
      }));
    } catch (error) {
      console.error('Failed to list conversations:', error);
      throw error;
    }
  },

  async createConversation({ title }) {
    try {
      const response = await api.post('/api/conversations', {
        title: title || 'New Conversation'
      });
      // Map snake_case to camelCase
      return {
        ...response.data,
        isPinned: response.data.is_pinned ?? false,
        messagesCount: response.data.messages_count,
        userId: response.data.user_id,
        createdAt: response.data.created_at
      };
    } catch (error) {
      console.error('Failed to create conversation:', error);
      throw error;
    }
  },

  async deleteConversation(id) {
    try {
      await api.delete(`/api/conversations/${id}`);
      return { success: true };
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  },

  async updateConversation(id, { title, isPinned }) {
    try {
      const response = await api.put(`/api/conversations/${id}`, {
        title,
        is_pinned: isPinned
      });
      // Map snake_case to camelCase
      return {
        ...response.data,
        isPinned: response.data.is_pinned ?? false,
        messagesCount: response.data.messages_count,
        userId: response.data.user_id,
        createdAt: response.data.created_at
      };
    } catch (error) {
      console.error('Failed to update conversation:', error);
      throw error;
    }
  },

  async listMessages(conversationId) {
    try {
      const response = await api.get(`/api/${conversationId}/messages`, {
        params: {
          limit: 100,
          order_desc: false  // Oldest first for chat display
        }
      });
      // Map backend 'sender' field to frontend 'role' field
      return response.data.map(msg => ({
        ...msg,
        role: msg.sender
      }));
    } catch (error) {
      console.error('Failed to list messages:', error);
      throw error;
    }
  },

  async createMessage({ conversationId, role, content }) {
    try {
      const response = await api.post(`/api/${conversationId}/messages`, {
        content,
        sender: role  // Backend expects 'sender' field
      });
      // Map backend 'sender' field to frontend 'role' field
      return {
        ...response.data,
        role: response.data.sender
      };
    } catch (error) {
      console.error('Failed to create message:', error);
      throw error;
    }
  },
};

const svc = useMock ? mockApi : realApi;

export const listConversations = svc.listConversations;
export const createConversation = svc.createConversation;
export const deleteConversation = svc.deleteConversation;
export const updateConversation = svc.updateConversation || ((id, data) => Promise.resolve({ id, ...data }));
export const listMessages = svc.listMessages;
export const createMessage = svc.createMessage;

export default {
  listConversations,
  createConversation,
  deleteConversation,
  updateConversation,
  listMessages,
  createMessage,
};


