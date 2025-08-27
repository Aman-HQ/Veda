import axios from 'axios';
import authStore from '../stores/authStore.js';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  timeout: 10000,
});

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
  (error) => {
    // Minimal resilience: just pass the error through for now
    return Promise.reject(error);
  }
);

export default instance;


