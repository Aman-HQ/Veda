export default function Topbar({ onMenuClick }) {
  return (
    <header className="fixed top-0 inset-x-0 h-14 backdrop-blur supports-[backdrop-filter]:bg-white/60 bg-white/80 dark:bg-slate-900/80 border-b border-slate-200/60 dark:border-slate-800 z-40">
      <div className="h-full max-w-screen-2xl mx-auto flex items-center gap-2 px-3 sm:px-4">
        {/* Left: Logo + App name */}
        <div className="flex items-center gap-2 select-none">
          <div className="h-6 w-6 rounded bg-gradient-to-br from-indigo-500 to-violet-500" />
          <span className="font-semibold text-slate-800 dark:text-slate-100">Veda</span>
        </div>

        {/* Right: User avatar + Menu toggle */}
        <div className="ml-auto flex items-center gap-2">
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


