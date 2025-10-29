let inMemoryAccessToken = null;

const REFRESH_TOKEN_KEY = 'refreshToken';

const authStore = {
  setTokens({ accessToken, refreshToken }) {
    inMemoryAccessToken = accessToken || null;
    if (refreshToken) {
      try {
        window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      } catch (e) {
        // ignore storage errors in mock
      }
    }
  },

  clear() {
    inMemoryAccessToken = null;
    try {
      window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    } catch (e) {
      // ignore
    }
  },

  getAccessToken() {
    return inMemoryAccessToken;
  },

  getRefreshToken() {
    try {
      return window.localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (e) {
      return null;
    }
  },
  
  hasRefreshToken() {
    return Boolean(this.getRefreshToken());
  },
};

export default authStore;


