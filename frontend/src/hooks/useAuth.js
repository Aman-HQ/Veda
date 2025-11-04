import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authStore from '../stores/authStore.js';
import api from '../services/api.js';

export default function useAuth() {
  const navigate = useNavigate();

  const login = useCallback(async ({ email, password }) => {
    try {
      const response = await api.post('/api/auth/login', {
        email,
        password
      });
      
      const { access_token, refresh_token } = response.data;
      authStore.setTokens({ 
        accessToken: access_token, 
        refreshToken: refresh_token 
      });
      
      navigate('/chat', { replace: true });
      return { accessToken: access_token, refreshToken: refresh_token };
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(
        error.response?.data?.detail || 'Login failed. Please check your credentials.'
      );
    }
  }, [navigate]);

  const register = useCallback(async ({ name, email, password }) => {
    try {
      // First, register the user
      await api.post('/api/auth/register', {
        name,
        email,
        password
      });
      
      // Then automatically log them in
      const response = await api.post('/api/auth/login', {
        email,
        password
      });
      
      const { access_token, refresh_token } = response.data;
      authStore.setTokens({ 
        accessToken: access_token, 
        refreshToken: refresh_token 
      });
      
      navigate('/chat', { replace: true });
      return { accessToken: access_token, refreshToken: refresh_token };
    } catch (error) {
      console.error('Registration failed:', error);
      throw new Error(
        error.response?.data?.detail || 'Registration failed. Please try again.'
      );
    }
  }, [navigate]);

  const refreshToken = useCallback(async () => {
    try {
      const currentRefreshToken = authStore.getRefreshToken();
      if (!currentRefreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await api.post('/api/auth/refresh', {
        refresh_token: currentRefreshToken
      });
      
      const { access_token, refresh_token } = response.data;
      authStore.setTokens({ 
        accessToken: access_token, 
        refreshToken: refresh_token 
      });
      
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear tokens and throw error (let caller handle navigation)
      authStore.clear();
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    authStore.clear();
    navigate('/login', { replace: true });
  }, [navigate]);

  const isAuthed = useCallback(() => {
    return Boolean(authStore.getAccessToken());
  }, []);

  const getMe = useCallback(async () => {
    try {
      const response = await api.get('/api/auth/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get user info:', error);
      throw error;
    }
  }, []);

  return { login, logout, register, refreshToken, isAuthed, getMe };
}



