import * as mockApi from './mockApi.js';
import api from './api.js';

// Default to mock API during Phase F. If the env var is absent, treat as 'true'.
const useMock = (import.meta.env.VITE_USE_MOCK_API ?? 'true') === 'true';

const realApi = {
  async listConversations() {
    try {
      const response = await api.get('/api/conversations');
      return response.data;
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
      return response.data;
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

  async listMessages(conversationId) {
    try {
      const response = await api.get(`/api/${conversationId}/messages`, {
        params: {
          limit: 100,
          order_desc: false  // Oldest first for chat display
        }
      });
      return response.data;
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
      return response.data;
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
export const listMessages = svc.listMessages;
export const createMessage = svc.createMessage;

export default {
  listConversations,
  createConversation,
  deleteConversation,
  listMessages,
  createMessage,
};


