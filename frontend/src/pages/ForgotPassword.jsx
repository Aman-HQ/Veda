import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import AuthLayout from '../components/Layout/AuthLayout.jsx';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showResend, setShowResend] = useState(false);

  const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

  const handleForgotPassword = async (e, isResend = false) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const endpoint = isResend ? '/resend-password-reset' : '/forgot-password';
      const response = await axios.post(`${apiBase}/api/auth${endpoint}`, {
        email: email
      });

      setMessage(response.data.message);
      setShowResend(true); // Show resend option after first send
      if (!isResend) {
        // Keep email in input for resend functionality
      }
    } catch (err) {
      console.error('Password reset error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-7 w-[500px] sm:w-[440px]">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-8 text-center whitespace-nowrap inline-flex items-center justify-center">
          Forgot Password
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-2 text-center">
          Enter your email address and we'll send you a link to reset your password.
        </p>

        <form onSubmit={(e) => handleForgotPassword(e, false)} className="space-y-3">
          <label className="block" htmlFor="forgot-email">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Email</span>
            <input
              id="forgot-email"
              type="email"
              required
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              placeholder="you@example.com"
            />
          </label>

          {message && (
            <div className="rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3">
              <p className="text-sm text-green-800 dark:text-green-200">{message}</p>
            </div>
          )}

          {error && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          <button
            type="submit"
            className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        {showResend && message && (
          <div className="mt-4">
            <button
              onClick={(e) => handleForgotPassword(e, true)}
              disabled={loading}
              className="w-full py-2 px-4 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Didn't receive email? Resend
            </button>
          </div>
        )}

        <div className="mt-6 text-center">
          <Link 
            to="/login" 
            className="text-indigo-600 dark:text-indigo-400 hover:underline text-sm"
          >
            Back to Login
          </Link>
        </div>

        <div className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
          <p>Check your spam folder if you don't see the email.</p>
        </div>
      </div>
    </AuthLayout>
  );
}
