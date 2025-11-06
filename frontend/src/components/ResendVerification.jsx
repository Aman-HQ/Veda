import { useState } from 'react';
import { Link } from 'react-router-dom';
import AuthLayout from './Layout/AuthLayout.jsx';

export default function ResendVerification() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleResend = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setLoading(true);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE}/api/auth/resend-verification`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email: email.toLowerCase().trim() }),
        }
      );

      const data = await response.json();

      // Always show success message (don't reveal if account exists for security)
      if (response.ok) {
        setMessage(data.message || 'If an account exists for that email, a verification email has been sent.');
        setEmail(''); // Clear email field on success
      } else {
        // Even on error, show generic message (security best practice)
        setMessage('If an account exists for that email, a verification email has been sent.');
        setEmail('');
      }
    } catch (err) {
      console.error('Resend verification error:', err);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-6 text-center">
          Resend Verification Email
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 text-center">
          Enter your email to receive a new verification link
        </p>

        <form onSubmit={handleResend} className="space-y-4" aria-label="Resend verification form">
          <label className="block" htmlFor="resend-email">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Email</span>
            <input
              id="resend-email"
              type="email"
              required
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
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
            className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? 'Sending...' : 'Resend Verification Email'}
          </button>
        </form>

        <div className="mt-4 text-center space-y-2">
          <Link to="/login" className="block text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
            Back to Login
          </Link>
          <Link to="/register" className="block text-sm text-slate-600 dark:text-slate-400 hover:underline">
            Don't have an account? Register
          </Link>
        </div>
      </div>
    </AuthLayout>
  );
}
