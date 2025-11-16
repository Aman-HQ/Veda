import { useEffect, useRef, useState } from 'react';
import useAuth from '../../hooks/useAuth.js';
import UserProfileMenu from './UserProfileMenu.jsx';
import SettingsPanel from './SettingsPanel.jsx';

export default function Sidebar({ open, onClose, children }) {
  const { user, logout } = useAuth();
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);
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
        className={`sm:static fixed inset-y-0 left-0 z-40 w-72 border-r flex flex-col transition-all duration-300 ease-out sm:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
        style={{
          backgroundColor: 'var(--sidebar-bg)',
          borderColor: 'var(--sidebar-border)'
        }}
        aria-label="Conversation navigation"
        role="navigation"
        ref={panelRef}
        tabIndex={-1}
      >
        <div 
          className="h-14 sm:hidden flex items-center px-3 border-b transition-colors duration-300"
          style={{ borderColor: 'var(--sidebar-border)' }}
        >
          <button
            className="h-9 w-9 inline-flex items-center justify-center rounded-md border outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
            style={{
              borderColor: 'var(--sidebar-border)',
              color: 'var(--sidebar-text)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            onClick={onClose}
            aria-label="Close sidebar"
          >
            ×
          </button>
        </div>
        {children ? (
          children
        ) : (
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            <div 
              className="text-sm px-3 py-2 transition-colors duration-300"
              style={{ color: 'var(--sidebar-text-secondary)' }}
            >
              No sidebar content
            </div>
          </div>
        )}
        <div 
          className="flex-shrink-0 p-3 border-t transition-colors duration-300"
          style={{ borderColor: 'var(--sidebar-border)' }}
        >
          {/* User Profile Menu */}
          {user && (
            <UserProfileMenu 
              user={user} 
              onLogout={logout}
              onOpenSettings={() => setSettingsPanelOpen(true)}
            />
          )}
        </div>
      </aside>

      {/* Settings Panel */}
      <SettingsPanel 
        isOpen={settingsPanelOpen}
        onClose={() => setSettingsPanelOpen(false)}
      />
    </>
  );
}


