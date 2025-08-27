import { useState } from 'react';
import useAuth from '../hooks/useAuth.js';
import AuthLayout from '../components/Layout/AuthLayout.jsx';

export default function Register() {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register({ name, email, password });
    } catch (err) {
      setError('Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  return (
    <AuthLayout>
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow p-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">Create account</h1>
        <form onSubmit={onSubmit} className="space-y-3" aria-label="Register form">
          <label className="block" htmlFor="register-name">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Name</span>
            <input
              id="register-name"
              type="text"
              required
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label className="block" htmlFor="register-email">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Email</span>
            <input
              id="register-email"
              type="email"
              required
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label className="block" htmlFor="register-password">
            <span className="block text-sm text-slate-700 dark:text-slate-300">Password</span>
            <input
              id="register-password"
              type="password"
              required
              className="mt-1 w-full rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error && <div className="text-red-500 text-sm">{error}</div>}
          <button
            type="submit"
            className="w-full py-2 px-4 rounded-md bg-slate-900 dark:bg-slate-800 text-white font-semibold hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <div className="my-4 text-center text-xs text-slate-500 dark:text-slate-400">or</div>
        <button
          type="button"
          className="w-full py-2 px-4 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white font-semibold border border-slate-300 dark:border-slate-600 hover:bg-indigo-50 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          disabled={!googleClientId}
        >
          Continue with Google {googleClientId ? '' : '(no-client-id)'}
        </button>
        <div className="mt-4 text-center">
          <a href="/login" className="text-indigo-600 hover:underline text-sm">Already have an account? Login</a>
        </div>
      </div>
    </AuthLayout>

    
  );
}
