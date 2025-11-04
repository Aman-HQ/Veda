import { Navigate, Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import authStore from '../stores/authStore.js';
import useAuth from '../hooks/useAuth.js';
import api from '../services/api.js';  //Frontend axios instance (NOT backend!)

export default function ProtectedRoute() {
  const { refreshToken } = useAuth();
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    let isMounted = true; // Add this for cleanup OR ADDED CAUSE: Prevent state updates after unmount

    const checkAuth = async () => {
      console.log('ProtectedRoute: Verifying authentication...'); // ADDED: Debug log
      
      // MODIFIED: Check if tokens exist
      const accessToken = authStore.getAccessToken();
      const refreshTokenvalue = authStore.getRefreshToken();

      if (!accessToken && !refreshTokenvalue) {
        console.log('ProtectedRoute: No tokens found'); // ADDED: Debug log
        if (isMounted) { // ADDED: Check if mounted
          setIsAuthenticated(false);
          setIsChecking(false);
        }
        return;
      }

      // ADDED: If we have access token, validate it with backend
      if (accessToken) {
        try {
          console.log('ProtectedRoute: Validating access token...'); // ADDED: Debug log
          // Calls backend over HTTP ----
          const response = await api.get('/api/auth/me'); // ✅ Actually validates the token
          
          if (response.data && response.data.email) {
            console.log('ProtectedRoute: User authenticated:', response.data.email); // ADDED: Debug log
            if (isMounted) { // ADDED: Check if mounted
              setIsAuthenticated(true); // ✅ Only trusts if backend confirms
              setIsChecking(false);
            }
            return;
          }
        } catch (error) {
          console.log('ProtectedRoute: Access token invalid, trying refresh...'); // ADDED: Debug log
          // Access token invalid, will try refresh below
        }
      }

      // MODIFIED: Try to refresh if we have refresh token
      if (refreshToken) {
        try {
          console.log('ProtectedRoute: Attempting token refresh...'); // ADDED: Debug log
          await refreshToken();
          if (isMounted) { // ADDED: Check if mounted
            setIsAuthenticated(true);
            setIsChecking(false); // ADDED: Was missing
          }
        } catch (error) {
          console.error('ProtectedRoute: Refresh failed:', error);
          authStore.clearTokens(); // ADDED: Clear invalid tokens
          if (isMounted) { // ADDED: Check if mounted
            setIsAuthenticated(false);
            setIsChecking(false); // ADDED: Was missing
          }
        }
      } else {
        console.log('ProtectedRoute: No refresh token available'); // ADDED: Debug log
        authStore.clearTokens(); // ADDED: Clear invalid tokens
        if (isMounted) { // ADDED: Check if mounted
          setIsAuthenticated(false);
          setIsChecking(false);
        }
      }
    };

    checkAuth();

    // ADDED: Cleanup function
    return () => {
      isMounted = false;
    };
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
    console.log('ProtectedRoute: Redirecting to login'); // ADDED: Debug log
    return <Navigate to="/login" replace />;
  }

  console.log('ProtectedRoute: Rendering protected content'); // ADDED: Debug log
  return <Outlet />;
}



