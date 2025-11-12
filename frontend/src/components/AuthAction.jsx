import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { auth } from '../firebase';
import { 
  confirmPasswordReset, 
  verifyPasswordResetCode, 
  applyActionCode,
  checkActionCode,
  signInWithEmailAndPassword,
  signInWithCustomToken
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
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
      // Step 1: Get email from the action code BEFORE applying it
      console.log('🔍 Checking email verification code...');
      const info = await checkActionCode(auth, oobCode);
      const userEmail = info.data.email;
      console.log('📧 Email to verify:', userEmail);
      
      // Step 2: Apply the email verification code (this marks email as verified in Firebase)
      let codeAlreadyUsed = false;

      try {
      await applyActionCode(auth, oobCode);
      console.log('✅ Email verification code applied successfully');
      } catch (applyError) {
        // If code was already used, that's okay - email is already verified
        if (applyError.code === 'auth/invalid-action-code') {
          console.log('ℹ️ Verification code already used (email already verified)');
          
          // Since we already got the email from checkActionCode above,
          // we know the code was valid at some point. If it's invalid now,
          // it's likely already been used. Set flag to skip duplicate processing.
          codeAlreadyUsed = true;
          console.log('✅ Assuming email already verified (code already applied)');
        } else {
          throw applyError; // Re-throw other errors
        }
      }
      
      // If code was already used and we're in React StrictMode, skip the rest
      if (codeAlreadyUsed) {
        console.log('⏭️ Skipping duplicate verification attempt (React StrictMode)');
        setVerifying(false);
        return;
      }

      setSuccess(true);
      
      // Step 3: Sign in with Firebase to get ID token (CRITICAL STEP)
      try {
        console.log('🔐 Getting Firebase ID token for verified user...');
      
        // CRITICAL: We need to sign in to get an ID token
        // Since we don't have the user's password, we use the custom token approach
        
        // Method 1: If user is already signed in (from applyActionCode)
        let idToken = null;
        const currentUser = auth.currentUser;
        
        if (currentUser && currentUser.email === userEmail) {
          // User is signed in, reload to get updated email_verified status
          await currentUser.reload();
          idToken = await currentUser.getIdToken(true); // Force refresh
          console.log('✅ Got ID token from current user');
        } else {
          // Method 2: User not signed in - need backend to create custom token
          console.log('⚠️ User not signed in, requesting custom token from backend...');
          
          // Call backend to get custom token
          const customTokenResponse = await axios.post(
            `${apiBase}/api/auth/get-custom-token`,
            { email: userEmail }
          );
          
          const customToken = customTokenResponse.data.custom_token;
          
          // Sign in with custom token
          const userCredential = await signInWithCustomToken(auth, customToken);
          idToken = await userCredential.user.getIdToken(true);
          console.log('✅ Got ID token from custom token sign-in');
        }

        console.log('🔐 Requesting auto-login from backend with ID token...');
        
        // Call backend with Firebase ID token
        const response = await axios.post(
          `${apiBase}/api/auth/verify-and-login`, 
          { firebase_id_token: idToken },
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );
        
        console.log('✅ Backend response:', response.data);
        
        // Store tokens using auth store
        const { access_token, refresh_token } = response.data;
        
        if (access_token && refresh_token) {
          authStore.setTokens({
            accessToken: access_token,
            refreshToken: refresh_token
          });
          
          console.log('✅ Tokens stored, redirecting to chat...');
          
          setVerifying(false);

          // Navigate to chat page
          setTimeout(() => {
            navigate('/chat', { 
              replace: true,
              state: {
                message: 'Email verified successfully! Welcome!',
                type: 'success'
              }
            });
          }, 2000);
        } else {
          throw new Error('Invalid response from server');
        }
        
      } catch (error) {
        console.error('❌ Auto-login failed:', error);
        console.error('Error details:', error.response?.data || error.message);
        
        // Better error handling - show specific error if available
      const errorMessage = error.response?.data?.detail || 'Auto-login failed. Please login manually.';
      
      setError(`Email verified! ${errorMessage}`);
      setVerifying(false);

        // Fallback: Show success and redirect to login
        setTimeout(() => {
          navigate('/login', {
            state: {
              message: `Email verified! ${errorMessage}`,
              type: 'success'
            }
          });
        }, 3000);
      }
      
    } catch (error) {
      console.error('❌ Email verification error:', error);
      
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
              <div className="relative">
                <input
                  id="new-password"
                  type={showNewPassword ? "text" : "password"}
                  required
                  minLength={8}
                  className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 pr-10 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={loading}
                  placeholder="Enter new password (min 8 characters)"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-1 top-1/2 -translate-y-1/2 mt-0.5 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-all focus:outline-none shadow p-6 bg-transparent"
                  aria-label={showNewPassword ? "Hide password" : "Show password"}
                >
                  {showNewPassword ? (
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

            <label className="block" htmlFor="confirm-password">
              <span className="block text-sm text-slate-700 dark:text-slate-300">Confirm Password</span>
              <div className="relative">
                <input
                  id="confirm-password"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  minLength={8}
                  className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 pr-10 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                  placeholder="Confirm your new password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-1 top-1/2 -translate-y-1/2 mt-0.5 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:text-slate-500 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-all focus:outline-none shadow p-6 bg-transparent"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? (
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