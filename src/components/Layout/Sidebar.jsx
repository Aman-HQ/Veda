import { useEffect, useRef } from 'react';

export default function Sidebar({ open, onClose, children }) {
  const panelRef = useRef(null);
  const previouslyFocusedRef = useRef(null);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // Focus trap: keep tab focus inside the sidebar while open
  useEffect(() => {
    if (!open) return;
    previouslyFocusedRef.current = document.activeElement;

    const panel = panelRef.current;
    if (!panel) return;

    const getFocusable = () => Array.from(
      panel.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      )
    );

    const focusables = getFocusable();
    if (focusables.length > 0) {
      focusables[0].focus();
    } else {
      panel.focus();
    }

    const handleKeyDown = (e) => {
      if (e.key !== 'Tab') return;
      const items = getFocusable();
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const isShift = e.shiftKey;
      const active = document.activeElement;
      if (!isShift && active === last) {
        e.preventDefault();
        first.focus();
      } else if (isShift && active === first) {
        e.preventDefault();
        last.focus();
      }
    };

    panel.addEventListener('keydown', handleKeyDown);
    return () => {
      panel.removeEventListener('keydown', handleKeyDown);
      if (previouslyFocusedRef.current && previouslyFocusedRef.current.focus) {
        previouslyFocusedRef.current.focus();
      }
    };
  }, [open]);

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={`sm:hidden fixed inset-0 bg-black/40 z-30 transition-opacity ${open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        onClick={onClose}
        aria-hidden
      />

      {/* Sidebar panel */}
      <aside
        className={`sm:static fixed inset-y-0 left-0 z-40 w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col transition-transform duration-200 ease-out sm:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
        aria-label="Conversation navigation"
        role="navigation"
        ref={panelRef}
        tabIndex={-1}
      >
        <div className="h-14 sm:hidden flex items-center px-3 border-b border-slate-200 dark:border-slate-800">
          <button
            className="h-9 w-9 inline-flex items-center justify-center rounded-md border border-slate-200 dark:border-slate-700 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            ×
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {children ? (
            children
          ) : (
            <div className="text-sm text-slate-500 dark:text-slate-400 px-2 py-2">No sidebar content</div>
          )}
        </div>
        <div className="p-3 border-t border-slate-200 dark:border-slate-800">
          <button className="w-full justify-center inline-flex items-center gap-2 px-3 py-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
            <span>Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
}


