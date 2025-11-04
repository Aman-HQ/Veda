// authStore.js - Authentication state management

let inMemoryAccessToken = null;

const REFRESH_TOKEN_KEY = 'refreshToken';

const authStore = {
  setTokens({ accessToken, refreshToken }) {
    inMemoryAccessToken = accessToken || null;
    if (refreshToken) {
      try {
        window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        console.log('AuthStore: Tokens stored successfully');
      } catch (e) {
        console.error('AuthStore: Failed to store refresh token', e);
      }
    }
  },

  // Clear all authentication tokens (alias for clearTokens)
  clear() {
    this.clearTokens();
  },

  // Clear all authentication tokens
  clearTokens() {
    inMemoryAccessToken = null;
    try {
      window.localStorage.removeItem(REFRESH_TOKEN_KEY);
      console.log('AuthStore: Tokens cleared');
    } catch (e) {
      console.error('AuthStore: Failed to clear tokens', e);
    }
  },

  // Get access token from memory
  getAccessToken() {
    return inMemoryAccessToken;
  },

  // Get refresh token from localStorage
  getRefreshToken() {
    try {
      return window.localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (e) {
      console.error('AuthStore: Failed to get refresh token', e);
      return null;
    }
  },
  
  // Get both tokens as an object
  getTokens() {
    return {
      accessToken: this.getAccessToken(),
      refreshToken: this.getRefreshToken()
    };
  },

  // Check if refresh token exists
  hasRefreshToken() {
    return Boolean(this.getRefreshToken());
  },

// Check if user is authenticated (has both tokens)
  isAuthenticated() {
    return Boolean(this.getAccessToken() && this.getRefreshToken());
  },
};

export default authStore;


