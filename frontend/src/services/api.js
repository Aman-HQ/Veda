import axios from 'axios';
import authStore from '../stores/authStore.js';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  timeout: 10000,
});

// Track if we're currently refreshing the token
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

instance.interceptors.request.use(
  (config) => {
    const token = authStore.getAccessToken?.();
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers['Authorization'] = 'Bearer ' + token;
            return instance(originalRequest);
          })
          .catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = authStore.getRefreshToken?.();
      
      if (!refreshToken) {
        // No refresh token, clear auth and reject
        authStore.clear?.();
        processQueue(new Error('No refresh token available'), null);
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        // Call refresh endpoint
        const response = await axios.post(
          `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/api/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token } = response.data;
        
        // Update tokens in store
        authStore.setTokens?.({
          accessToken: access_token,
          refreshToken: refresh_token
        });

        // Update the authorization header
        instance.defaults.headers.common['Authorization'] = 'Bearer ' + access_token;
        originalRequest.headers['Authorization'] = 'Bearer ' + access_token;

        // Process queued requests with new token
        processQueue(null, access_token);
        isRefreshing = false;

        // Retry original request
        return instance(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear auth and reject all queued requests
        processQueue(refreshError, null);
        authStore.clear?.();
        isRefreshing = false;
        
        // Optionally redirect to login (you can add navigation here if needed)
        // window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default instance;


