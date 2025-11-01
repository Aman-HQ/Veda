import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api.js';
import authStore from '../stores/authStore.js';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
          return;
        }

        if (!code) {
          console.error('No authorization code received');
          setError('No authorization code received');
          setLoading(false);
          setTimeout(() => navigate('/login', { replace: true }), 2000);
          return;
        }

        // MODIFIED: Exchange code for tokens - wait for completion
        let response;
        try {
          response = await api.post('/api/auth/google/callback', {
          code,
          state: state || undefined
        });
        } catch (err) {
          // MODIFIED: Better error handling with specific messages
          console.error('OAuth callback error:', err);

          let errorMessage = 'Authentication failed. Please try again.';
          
          if (err.response?.status === 403) {
            errorMessage = 'Your Google account is not authorized. This app is in testing mode.';
          } else if (err.response?.status === 400) {
            errorMessage = 'Invalid authorization code. Please try again.';
          } else if (err.response?.data?.detail) {
            errorMessage = err.response.data.detail;
          }
          
          setError(errorMessage);
          setLoading(false);
          // Redirect to login after showing error
          setTimeout(() => navigate('/login', { replace: true }), 3000);
          return; // CRITICAL: Exit early on error - prevents token storage
        }

        // MODIFIED: Only store tokens if backend succeeded
        const { access_token, refresh_token } = response.data;
        
        if (!access_token || !refresh_token) {
          throw new Error('Invalid token response from server');
        }

        // Store tokens only after successful validation
        authStore.setTokens({
          accessToken: access_token,
          refreshToken: refresh_token
        });

        // MODIFIED: Successfully authenticated - redirect immediately
        navigate('/chat', { replace: true });

      } catch (err) {
        // MODIFIED: Catch-all error handler
        console.error('Unexpected OAuth error:', err);
        setError('An unexpected error occurred. Please try again.');
        setLoading(false);
        // Redirect to login after showing error
        setTimeout(() => navigate('/login', { replace: true }), 2000);
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate]);

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
