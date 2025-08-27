import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authStore from '../stores/authStore.js';

function fakeToken(prefix) {
  const rand = Math.random().toString(36).slice(2);
  return `${prefix}.${rand}`;
}

export default function useAuth() {
  const navigate = useNavigate();

  const login = useCallback(async ({ email, password }) => {
    await new Promise((resolve) => setTimeout(resolve, 400));
    const accessToken = fakeToken('access');
    const refreshToken = fakeToken('refresh');
    authStore.setTokens({ accessToken, refreshToken });
    navigate('/chat', { replace: true });
    return { accessToken, refreshToken };
  }, [navigate]);

  const register = useCallback(async ({ name, email, password }) => {
    await new Promise((resolve) => setTimeout(resolve, 600));
    const accessToken = fakeToken('access');
    const refreshToken = fakeToken('refresh');
    authStore.setTokens({ accessToken, refreshToken });
    navigate('/chat', { replace: true });
    return { accessToken, refreshToken };
  }, [navigate]);

  const logout = useCallback(() => {
    authStore.clear();
    navigate('/login', { replace: true });
  }, [navigate]);

  const isAuthed = useCallback(() => {
    return Boolean(authStore.getAccessToken());
  }, []);

  return { login, logout, register, isAuthed };
}


