import { useEffect, useState } from 'react';
import Topbar from '../Layout/Topbar.jsx';
import Sidebar from '../Layout/Sidebar.jsx';
import { Outlet } from 'react-router-dom';
import uiStore from '../../stores/uiStore.js';

export default function ChatLayout({ sidebarContent, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(uiStore.getState().sidebarOpen);

  useEffect(() => {
    const unsub = uiStore.subscribe((s) => setSidebarOpen(s.sidebarOpen));
    return unsub;
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden flex">
      {/* Sidebar with its own header - extends to top */}
      <div className={`relative transition-all duration-300 ease-in-out overflow-hidden ${
        sidebarOpen ? 'w-72' : 'w-0'
      }`}>
        <div 
          className="w-72 h-full border-r flex flex-col transition-colors duration-300"
          style={{
            backgroundColor: 'var(--sidebar-bg)',
            borderColor: 'var(--sidebar-border)'
          }}
        >
          {/* Sidebar Header */}
          <div 
            className="h-14 flex items-center px-4 gap-3 border-b flex-shrink-0 transition-colors duration-300"
            style={{
              backgroundColor: 'var(--sidebar-bg)',
              borderColor: 'var(--sidebar-border)'
            }}
          >
            <button
              aria-label="Toggle sidebar"
              className="inline-flex items-center justify-center h-8 w-8 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
              style={{
                color: 'var(--sidebar-text)'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              onClick={() => uiStore.toggleSidebar()}
            >
              <span className="text-xl">☰</span>
            </button>
            <span 
              className="font-semibold text-lg transition-colors duration-300"
              style={{ color: 'var(--sidebar-text)' }}
            >
              Veda
            </span>
          </div>
          
          {/* Sidebar Content */}
          <div className="flex-1 overflow-hidden">
            <Sidebar open={sidebarOpen} onClose={() => uiStore.closeSidebar()}>
              {sidebarContent}
            </Sidebar>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 min-w-0 h-full flex flex-col relative">
        {/* Completely transparent top bar */}
        <div 
          className="h-12 flex-shrink-0 transition-all duration-300"
          style={{
            backgroundColor: 'transparent',
            borderColor: 'transparent'
          }}
        >
          <Topbar onMenuClick={() => uiStore.toggleSidebar()} />
        </div>

        {/* Main chat area with enhanced glass effect */}
        <main 
          className="flex-1 min-h-0 flex flex-col backdrop-blur-sm shadow-lg transition-all duration-300"
          style={{
            backgroundColor: 'transparent'
          }}
        >
          {children ? children : <Outlet />}
        </main>
      </div>
    </div>
  );
}


