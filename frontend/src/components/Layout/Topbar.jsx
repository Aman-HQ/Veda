import { Link } from 'react-router-dom';
import useAuth from '../../hooks/useAuth.js';

export default function Topbar({ onMenuClick }) {
  const { user } = useAuth();
  
  return (
    <header className="fixed top-0 inset-x-0 h-14 backdrop-blur supports-[backdrop-filter]:bg-white/60 bg-white/80 dark:bg-slate-900/80 border-b border-slate-200/60 dark:border-slate-800 z-40">
      <div className="h-full max-w-screen-2xl mx-auto flex items-center gap-2 px-3 sm:px-4">
        {/* Left: Logo + App name */}
        <div className="flex items-center gap-2 select-none">
          <div className="h-6 w-6 rounded bg-gradient-to-br from-indigo-500 to-violet-500" />
          <span className="font-semibold text-slate-800 dark:text-slate-100">Veda</span>
        </div>

        {/* Right: Admin Panel Link + User avatar + Menu toggle */}
        <div className="ml-auto flex items-center gap-2">
          {/* Admin Panel Button - Only visible for admin users */}
          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md 
                bg-white/100 text-black text-sm font-medium 
                border border-purple-700 
                shadow-sm transition-colors 
                focus-visible:ring-2 focus-visible:ring-black/500 focus-visible:ring-offset-2"
              title="Admin Panel"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
              <span className="hidden sm:inline">Admin</span>
            </Link>
          )}
          
          <button aria-label="User" className="inline-flex items-center justify-center h-9 w-9 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 transition-colors">
            <span className="text-sm">😊</span>
          </button>
          <button
            aria-label="Toggle sidebar"
            className="inline-flex items-center justify-center h-9 w-9 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 transition-colors"
            onClick={onMenuClick}
          >
            <span className="text-xl">≡</span>
          </button>
        </div>
      </div>
    </header>
  );
}


