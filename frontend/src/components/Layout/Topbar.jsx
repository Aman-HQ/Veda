import { Link } from 'react-router-dom';
import useAuth from '../../hooks/useAuth.js';

export default function Topbar({ onMenuClick }) {
  const { user } = useAuth();
  
  return (
    <header className="h-full">
      <div className="h-full max-w-screen-2xl mx-auto flex items-center gap-2 px-4">
        {/* Right: Admin Panel Link + User avatar (no menu toggle - it's in sidebar now) */}
        <div className="ml-auto flex items-center gap-2">
          {/* Admin Panel Button - Only visible for admin users */}
          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md 
                bg-white/80 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 text-sm font-medium 
                border border-slate-300 dark:border-slate-600 
                backdrop-blur-md shadow-sm hover:bg-white dark:hover:bg-slate-700 transition-colors 
                focus-visible:ring-2 focus-visible:ring-blue-500"
              title="Admin Panel"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
              <span className="hidden sm:inline">Admin</span>
            </Link>
          )}
          
          <button 
            aria-label="User" 
            className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-slate-100/80 dark:bg-slate-800/80 backdrop-blur-md border border-slate-200 dark:border-slate-700 outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-colors"
          >
            <span className="text-sm">😊</span>
          </button>
        </div>
      </div>
    </header>
  );
}


