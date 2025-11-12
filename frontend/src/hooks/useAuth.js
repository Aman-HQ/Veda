import { useCallback, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authStore from '../stores/authStore.js';
import api from '../services/api.js';

export default function useAuth() {
  const navigate = useNavigate();
  // Read user from authStore instead of local state
  const [user, setUser] = useState(authStore.getUser());
  const [isAuthenticated, setIsAuthenticated] = useState(!!authStore.getUser());
  const [loading, setLoading] = useState(true);  // Add loading state

  // Fetch user data on mount if tokens exist but no user data
  useEffect(() => {
    const loadUser = async () => {
      // If we already have user data, no need to fetch
      if (authStore.getUser()) {
        setUser(authStore.getUser());
        setIsAuthenticated(true);
        setLoading(false);
        return;
      }

      // If we have access token, fetch user data
      if (authStore.getAccessToken()) {
        try {
          const userData = await getMe();
          authStore.setUser(userData);  // Store in authStore
          setUser(userData);
          setIsAuthenticated(true);
          setLoading(false);
          return;
        } catch (error) {
          console.error('Failed to load user with access token:', error);
          // Access token might be expired, try refresh token below
        }
      }

      // If no access token but we have refresh token, refresh it first
      if (authStore.getRefreshToken() && !authStore.getAccessToken()) {
        try {
          console.log('No access token found, attempting to refresh...');
          await refreshToken();
          // After refresh, fetch user data
          const userData = await getMe();
          authStore.setUser(userData);
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Failed to refresh token or load user:', error);
          // Refresh failed, clear everything
          authStore.clear();
          setUser(null);
          setIsAuthenticated(false);
        }
      }
      
      setLoading(false);  // Done loading regardless of success/failure
    };
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);  // Only run on mount

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
      
      // Fetch user data after login
      const userData = await getMe();
      authStore.setUser(userData);  // Store in authStore
      setUser(userData);
      setIsAuthenticated(true);
      
      navigate('/chat', { replace: true });
      return { accessToken: access_token, refreshToken: refresh_token };
    } catch (error) {
      console.error('Login failed:', error);
      
      // Pass the specific error message from backend
      const errorMessage = error.response?.data?.detail || 'Login failed. Please check your credentials.';
      throw new Error(errorMessage);
    }
  }, [navigate]);

  const register = useCallback(async ({ name, email, password }) => {
    try {
      // Register the user (DON'T auto-login - user needs to verify email first)
      const response = await api.post('/api/auth/register', {
        name,
        email,
        password
      });
      
      // Navigate to login with success message AND show resend link
      navigate('/login', { 
        replace: true,
        state: { 
          message: 'Registration successful! A verification email has been sent to your email. Please verify your account.',
          type: 'success',
          showResendLink: true
        }
      });
      
      return response.data;
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
    authStore.clear();  // This now clears user data too
    setUser(null);
    setIsAuthenticated(false);
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

  return { 
    login, 
    logout, 
    register, 
    refreshToken, 
    isAuthed, 
    getMe, 
    user, 
    isAuthenticated,
    loading  // Export loading state
  };
}



