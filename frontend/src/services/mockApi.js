// Simple in-memory mock API with simulated latency

const randomId = (prefix = '') => `${prefix}${Math.random().toString(36).slice(2, 10)}`;
const nowIso = () => new Date().toISOString();
const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms));

// Seed data
let conversations = [
  {
    id: randomId('c_'),
    title: 'Welcome to Veda',
    lastMessage: 'How can I help you today? 😊',
    createdAt: nowIso(),
    updatedAt: nowIso(),
    isPinned: false,
  },
];

const messagesByConversationId = {
  [conversations[0].id]: [
    {
      id: randomId('m_'),
      conversationId: conversations[0].id,
      role: 'assistant',
      content: 'Hi! I am Veda, your healthcare assistant. How can I help you today? 😊',
      createdAt: nowIso(),
    },
  ],
};

export async function listConversations() {
  await delay(250);
  // Return a shallow copy to prevent external mutation
  return conversations.map((c) => ({ ...c }));
}

export async function createConversation({ title }) {
  await delay(200);
  const conversation = {
    id: randomId('c_'),
    title: title || 'New conversation',
    lastMessage: '',
    createdAt: nowIso(),
    updatedAt: nowIso(),
    isPinned: false,
  };
  conversations.unshift(conversation);
  messagesByConversationId[conversation.id] = [];
  return { id: conversation.id, ...conversation };
}

export async function updateConversation(id, { title, isPinned }) {
  await delay(150);
  const conv = conversations.find((c) => c.id === id);
  if (!conv) {
    throw new Error('Conversation not found');
  }
  if (title !== undefined) {
    conv.title = title;
  }
  if (isPinned !== undefined) {
    conv.isPinned = isPinned;
  }
  conv.updatedAt = nowIso();
  return { ...conv };
}

export async function deleteConversation(id) {
  await delay(180);
  conversations = conversations.filter((c) => c.id !== id);
  delete messagesByConversationId[id];
  return { success: true };
}

export async function listMessages(conversationId) {
  await delay(260);
  const list = messagesByConversationId[conversationId] || [];
  return list.map((m) => ({ ...m }));
}

export async function createMessage({ conversationId, role, content }) {
  await delay(220);
  const message = {
    id: randomId('m_'),
    conversationId,
    role,
    content,
    createdAt: nowIso(),
  };
  if (!messagesByConversationId[conversationId]) {
    messagesByConversationId[conversationId] = [];
  }
  messagesByConversationId[conversationId].push(message);

  // Update conversation meta
  const conv = conversations.find((c) => c.id === conversationId);
  if (conv) {
    conv.lastMessage = content.slice(0, 140);
    conv.updatedAt = nowIso();
  }

  return { ...message };
}

export default {
  listConversations,
  createConversation,
  updateConversation,
  deleteConversation,
  listMessages,
  createMessage,
};


