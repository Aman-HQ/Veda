import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api.js';
import authStore from '../stores/authStore.js';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // CRITICAL FIX: Use useRef to prevent double execution in React 18 Strict Mode
  const hasProcessed = useRef(false);

  useEffect(() => {
    // CRITICAL: Prevent multiple executions (React 18 Strict Mode calls useEffect twice)
    if (hasProcessed.current) {
      console.log('OAuth callback already processed, skipping...');
      return;
    }
    
    hasProcessed.current = true;
    console.log('Processing OAuth callback...');

    const handleOAuthCallback = async () => {
      try {
        // Get authorization code from URL
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const errorParam = searchParams.get('error');

        // Check for OAuth errors from Google
        if (errorParam) {
          console.error('OAuth error from Google:', errorParam);
          setError(`Authentication cancelled or failed`);
          setLoading(false);
          setTimeout(() => navigate('/login', { replace: true }), 2000);
          return; // CRITICAL: Stop execution
        }

        if (!code) {
          console.error('No authorization code received');
          setError('No authorization code received');
          setLoading(false);
          setTimeout(() => navigate('/login', { replace: true }), 2000);
          return; // CRITICAL: Stop execution
        }

        console.log('Exchanging authorization code for tokens...');

        // Exchange code for tokens
        const response = await api.post('/api/auth/google/callback', {
          code,
          state: state || undefined
        });

        console.log('Token exchange successful, response received');

        // Validate response structure
        if (!response || !response.data) {
          console.error('Invalid response structure:', response);
          throw new Error('Invalid response from server');
        }

        // Validate response has tokens
        const { access_token, refresh_token } = response.data;
        
        if (!access_token || !refresh_token) {
          console.error('Missing tokens in response:', response.data);
          throw new Error('Invalid token response from server - missing tokens');
        }

        console.log('Tokens validated, storing...');

        // Store tokens only after ALL validations passed
        authStore.setTokens({
          accessToken: access_token,
          refreshToken: refresh_token
        });

        console.log('Tokens stored successfully, redirecting to chat...');

        // MODIFIED: Successfully authenticated - redirect immediately
        navigate('/chat', { replace: true });

      } catch (err) {
        // Handle ALL API errors here
        console.error('OAuth callback error:', err);
        
        // Clear any tokens that might have been stored
        authStore.clearTokens();
        
        let errorMessage = 'Authentication failed. Please try again.';
        
        // Handle specific error codes
        if (err.response?.status === 403) {
          errorMessage = 'Your Google account is not authorized. Please contact support.';
        } else if (err.response?.status === 400) {
          const detail = err.response?.data?.detail || '';
          
          // Authorization code already used or expired
          if (detail.includes('expired') || detail.includes('already been used')) {
            errorMessage = 'Session expired. Please try signing in again.';
          } else {
            errorMessage = detail || 'Invalid request. Please try again.';
          }
        } else if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        }
        
        setError(errorMessage);
        setLoading(false);

        // Redirect to login after showing error
        setTimeout(() => navigate('/login', { replace: true }), 3000);
      }
    };

    handleOAuthCallback();
  }, []); // CRITICAL: Empty dependency array to run only once

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 text-center">
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-slate-800 dark:text-white mb-2">
              Completing sign in...
            </h2>
            <p className="text-slate-600 dark:text-slate-400">
              Please wait while we authenticate your account.
            </p>
          </>
        ) : error ? (
          <>
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-slate-800 dark:text-white mb-2">
              Authentication Failed
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
            <p className="text-sm text-slate-500">Redirecting to login...</p>
          </>
        ) : null}
      </div>
    </div>
  );
}
