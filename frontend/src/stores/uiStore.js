// Lightweight UI store (no external deps). Inspired by Zustand's API.
// Usage:
//   import uiStore from './uiStore'
//   const unsubscribe = uiStore.subscribe((state) => { ... })
//   uiStore.getState()
//   uiStore.setState({ sidebarOpen: true })
//   uiStore.openSidebar()

const listeners = new Set();

const initialState = {
  sidebarOpen: true,
  activeConversationId: null,
  modal: { name: null, payload: null },
};

let state = { ...initialState };

function notify() {
  listeners.forEach((cb) => {
    try { cb(state); } catch (_) {}
  });
}

const uiStore = {
  // Subscribe to state changes
  subscribe(cb) {
    if (typeof cb === 'function') listeners.add(cb);
    return () => listeners.delete(cb);
  },

  // Get current state
  getState() {
    return state;
  },

  // Merge partial update and notify listeners
  setState(partial) {
    state = { ...state, ...(typeof partial === 'function' ? partial(state) : partial) };
    notify();
  },

  // Actions
  openSidebar() {
    uiStore.setState({ sidebarOpen: true });
  },
  closeSidebar() {
    uiStore.setState({ sidebarOpen: false });
  },
  toggleSidebar() {
    uiStore.setState((s) => ({ sidebarOpen: !s.sidebarOpen }));
  },

  setActiveConversation(id) {
    uiStore.setState({ activeConversationId: id ?? null });
  },

  openModal(name, payload = null) {
    uiStore.setState({ modal: { name, payload } });
  },
  closeModal() {
    uiStore.setState({ modal: { name: null, payload: null } });
  },
};

export default uiStore;


