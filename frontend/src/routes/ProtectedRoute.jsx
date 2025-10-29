import { Navigate, Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import authStore from '../stores/authStore.js';
import useAuth from '../hooks/useAuth.js';

export default function ProtectedRoute() {
  const { refreshToken } = useAuth();
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      // Check if we have an access token
      if (authStore.getAccessToken()) {
        setIsAuthenticated(true);
        setIsChecking(false);
        return;
      }

      // If no access token but have refresh token, try to refresh
      if (authStore.hasRefreshToken()) {
        try {
          await refreshToken();
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Auto-refresh failed:', error);
          setIsAuthenticated(false);
        }
      } else {
        setIsAuthenticated(false);
      }
      
      setIsChecking(false);
    };

    checkAuth();
  }, [refreshToken]);

  if (isChecking) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}


