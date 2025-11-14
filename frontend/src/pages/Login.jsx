import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth.js';
import AuthLayout from '../components/Layout/AuthLayout.jsx';

export default function Login() {
  const { login } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showResendLink, setShowResendLink] = useState(false);

  // Check for success message from password reset or registration
  useEffect(() => {
    if (location.state?.message && location.state?.type === 'success') {
      setSuccessMessage(location.state.message);
      
      // Show resend link if coming from registration
      if (location.state?.showResendLink) {
        setShowResendLink(true);
      }
      
      // Clear the message after 8 seconds
      const timer = setTimeout(() => {
        setSuccessMessage('');
        setShowResendLink(false);
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [location]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setShowResendLink(false);
    setLoading(true);
    try {
      await login({ email, password });
    } catch (err) {
      console.error('Login error:', err);
      
      // Check if error is due to unverified email
      // Look for either status code 403 or keywords in the error message
      const errorMsg = err.message || '';
      const isUnverifiedError = 
        errorMsg.includes('Email not verified') || 
        errorMsg.includes('verification email') ||
        errorMsg.includes('verify your account');
      
      if (isUnverifiedError) {
        setSuccessMessage('A verification email has been sent to your email. Please verify your account to login.');
        setShowResendLink(true);
        setError('');
      } else {
        setError(errorMsg || 'Login failed.');
        setShowResendLink(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  
  const handleGoogleLogin = () => {
    if (!googleClientId) {
      setError('Google OAuth is not configured');
      return;
    }
    
    // Build Google OAuth URL
    const redirectUri = `${window.location.origin}/oauth/callback`;
    const scope = 'openid email profile';
    const responseType = 'code';
    const accessType = 'offline';
    const prompt = 'consent';
    
    const googleAuthUrl = `https://accounts.google.com/o/oauth2/auth?client_id=${encodeURIComponent(googleClientId)}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&response_type=${responseType}&access_type=${accessType}&prompt=${prompt}`;
    
    // Redirect to Google
    window.location.href = googleAuthUrl;
  };

  return (
    <AuthLayout>
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-4 text-center">Login</h1>
        <form onSubmit={onSubmit} className="space-y-3" aria-label="Login form">
          <label className="block" htmlFor="login-email">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Email</span>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="block" htmlFor="login-password">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Password</span>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 pr-10 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors focus:outline-none"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                )}
              </button>
            </div>
          </label>
          <div className="flex justify-between items-center">
            {showResendLink ? (
              <a href="/resend-verification" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">
                Resend verification email
              </a>
            ) : (
              <span></span>
            )}
            <a href="/forgot-password" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">
              Forgot password?
            </a>
          </div>
          
          {successMessage && (
            <div className="rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3">
              <p className="text-sm text-green-800 dark:text-green-200">{successMessage}</p>
            </div>
          )}
          
          {error && <div className="text-red-500 text-sm">{error}</div>}
          
          <button
            type="submit"
            className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <div className="my-4 text-center text-xs text-slate-500 dark:text-slate-400">or</div>
        <button
          type="button"
          onClick={handleGoogleLogin}
          className="w-full py-2 px-4 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-white font-semibold border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 flex items-center justify-center gap-2"
          disabled={!googleClientId}
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>
        <div className="mt-4 text-center">
          <a href="/register" className="text-indigo-600 hover:underline text-sm">Don't have an account? Register</a>
        </div>
      </div>
    </AuthLayout>

  );
}

