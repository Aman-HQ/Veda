import * as mockApi from './mockApi.js';
// import api from './api.js'; // future real API client

// Default to mock API during Phase F. If the env var is absent, treat as 'true'.
const useMock = (import.meta.env.VITE_USE_MOCK_API ?? 'true') === 'true';

const realApi = {
  async listConversations() {
    throw new Error('Real API not implemented yet');
  },
  async createConversation({ title }) {
    throw new Error('Real API not implemented yet');
  },
  async deleteConversation(id) {
    throw new Error('Real API not implemented yet');
  },
  async listMessages(conversationId) {
    throw new Error('Real API not implemented yet');
  },
  async createMessage({ conversationId, role, content }) {
    throw new Error('Real API not implemented yet');
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


