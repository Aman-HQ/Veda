import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { auth } from '../firebase';
import { 
  confirmPasswordReset, 
  verifyPasswordResetCode, 
  applyActionCode,
  signInWithEmailAndPassword 
} from 'firebase/auth';
import axios from 'axios';
import AuthLayout from '../components/Layout/AuthLayout.jsx';
import authStore from '../stores/authStore';

export default function AuthAction() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Common states
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Password reset specific states
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [email, setEmail] = useState('');
  
  // Get parameters from URL
  const mode = searchParams.get('mode');
  const oobCode = searchParams.get('oobCode');
  const apiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  useEffect(() => {
    // Validate parameters
    if (!mode || !oobCode) {
      setError('Invalid action link. Please check your email and try again.');
      setVerifying(false);
      return;
    }

    // Route to appropriate handler based on mode
    switch (mode) {
      case 'resetPassword':
        handlePasswordResetVerification();
        break;
      case 'verifyEmail':
        handleEmailVerification();
        break;
      case 'recoverEmail':
        setError('Email recovery is not yet supported. Please contact support.');
        setVerifying(false);
        break;
      default:
        setError(`Unknown action type: ${mode}`);
        setVerifying(false);
    }
  }, [mode, oobCode]);

  // ========== PASSWORD RESET HANDLERS ==========
  
  const handlePasswordResetVerification = async () => {
    try {
      const userEmail = await verifyPasswordResetCode(auth, oobCode);
      setEmail(userEmail);
      setVerifying(false);
    } catch (error) {
      console.error('Password reset verification error:', error);
      
      // Handle specific Firebase errors
      if (error.code === 'auth/invalid-action-code') {
        setError('This password reset link is invalid or has already been used.');
      } else if (error.code === 'auth/expired-action-code') {
        setError('This password reset link has expired. Please request a new one.');
      } else {
        setError('Invalid or expired password reset link. Please request a new one.');
      }
      setVerifying(false);
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validation
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      // Step 1: Reset password in Firebase
      await confirmPasswordReset(auth, oobCode, newPassword);
      console.log('Password reset in Firebase successful');
      
      // Step 2: Sign in to get Firebase ID token
      const userCredential = await signInWithEmailAndPassword(auth, email, newPassword);
      const idToken = await userCredential.user.getIdToken();
      console.log('Got Firebase ID token');
      
      // Step 3: Sync with PostgreSQL
      await axios.post(`${apiBase}/api/auth/sync-password`, {
        firebase_id_token: idToken,
        new_password: newPassword
      });
      console.log('Password synced to PostgreSQL');

      setSuccess(true);
      
      // Navigate to login after success
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: 'Password reset successful! You can now log in with your new password.',
            type: 'success'
          } 
        });
      }, 2000);
      
    } catch (err) {
      console.error('Error resetting password:', err);
      
      // Handle specific errors
      if (err.response?.status === 401) {
        setError('Authentication failed. Please try resetting your password again.');
      } else if (err.response?.status === 404) {
        setError('User account not found. Please contact support.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.code === 'auth/weak-password') {
        setError('Password is too weak. Please use a stronger password.');
      } else if (err.code === 'auth/invalid-action-code') {
        setError('This reset link has already been used. Please request a new one.');
      } else {
        setError('Failed to reset password. Please try again or request a new reset link.');
      }
      setLoading(false);
    }
  };

  // ========== EMAIL VERIFICATION HANDLERS ==========

  const handleEmailVerification = async () => {
    try {
      // Apply the email verification code
      await applyActionCode(auth, oobCode);
      setSuccess(true);
      
      // Auto-login after verification
      const user = auth.currentUser;
      if (user) {
        try {
          // Get Firebase ID token
          const idToken = await user.getIdToken();
          
          // Call backend to auto-login
          const response = await axios.post(
            `${apiBase}/api/auth/verify-and-login`,
            { firebase_id_token: idToken }
          );
          
          // Store tokens using auth store
          const { access_token, refresh_token } = response.data;
          
          if (access_token && refresh_token) {
            authStore.setTokens({
              accessToken: access_token,
              refreshToken: refresh_token
            });
            
            setVerifying(false);
            
            // Navigate to chat page
            setTimeout(() => {
              navigate('/chat', { 
                replace: true,
                state: { 
                  autoLogin: true,
                  message: 'Email verified successfully!'
                }
              });
            }, 2000);
          } else {
            throw new Error('Invalid response from server');
          }
          
        } catch (error) {
          console.error('Auto-login failed:', error);
          setError('Verification successful, but auto-login failed. Please login manually.');
          setVerifying(false);
          setTimeout(() => navigate('/login'), 3000);
        }
      } else {
        setError('Verification successful! Please login to continue.');
        setVerifying(false);
        setTimeout(() => navigate('/login'), 2000);
      }
    } catch (error) {
      console.error('Email verification error:', error);
      
      // Provide user-friendly error messages
      if (error.code === 'auth/invalid-action-code') {
        setError('Verification link is invalid or has already been used.');
      } else if (error.code === 'auth/expired-action-code') {
        setError('Verification link has expired. Please request a new one.');
      } else {
        setError('Verification failed. Link may be expired or invalid.');
      }
      
      setVerifying(false);
    }
  };

  // ========== RENDER LOGIC ==========

  // Loading state while verifying code
  if (verifying) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400">
              {mode === 'resetPassword' ? 'Verifying reset code...' : 'Verifying your email...'}
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // Error state - verification failed
  if (error && !success) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-6 text-center">
            {mode === 'resetPassword' ? 'Reset Link Invalid' : 'Verification Failed'}
          </h1>
          <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 mb-6">
            <div className="text-center mb-3">
              <span className="text-4xl">❌</span>
            </div>
            <p className="text-sm text-red-800 dark:text-red-200 text-center">{error}</p>
          </div>
          <div className="space-y-4">
            {mode === 'resetPassword' && (
              <button
                onClick={() => navigate('/forgot-password')}
                className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Request New Reset Link
              </button>
            )}
            <button
              onClick={() => navigate('/login')}
              className="w-full py-2 px-4 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Back to Login
            </button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // ========== EMAIL VERIFICATION SUCCESS ==========
  if (mode === 'verifyEmail' && success) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <div className="text-center">
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
              Email Verified!
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-2">
              Your email has been successfully verified.
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Logging you in automatically...
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // ========== PASSWORD RESET SUCCESS ==========
  if (mode === 'resetPassword' && success) {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
          <div className="text-center">
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
              Password Reset Successful!
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-2">
              You can now log in with your new password.
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Redirecting to login...
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // ========== PASSWORD RESET FORM ==========
  if (mode === 'resetPassword') {
    return (
      <AuthLayout>
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6 w-[500px] sm:w-[440px]">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-9 text-center">
            Reset Password
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6 text-center">
            Enter your new password for <span className="font-medium text-slate-900 dark:text-slate-100">{email}</span>
          </p>

          <form onSubmit={handlePasswordReset} className="space-y-5">
            <label className="block" htmlFor="new-password">
              <span className="block text-sm text-slate-700 dark:text-slate-300">New Password</span>
              <input
                id="new-password"
                type="password"
                required
                minLength={8}
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={loading}
                placeholder="Enter new password (min 8 characters)"
              />
            </label>

            <label className="block" htmlFor="confirm-password">
              <span className="block text-sm text-slate-700 dark:text-slate-300">Confirm Password</span>
              <input
                id="confirm-password"
                type="password"
                required
                minLength={8}
                className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                placeholder="Confirm your new password"
              />
            </label>

            {error && (
              <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
                <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}

            {loading && !error && (
              <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  Resetting your password...
                </p>
              </div>
            )}

            <button
              type="submit"
              className="mt-2 w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Resetting Password...' : 'Reset Password'}
            </button>
          </form>

          <div className="mt-5 text-center">
            <button
              onClick={() => navigate('/login')}
              className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm"
              disabled={loading}
            >
              Back to Login
            </button>
          </div>

          <div className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
            <p>Make sure your password is at least 8 characters long.</p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  // Fallback
  return null;
}