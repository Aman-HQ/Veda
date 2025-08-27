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

    <div className="fixed inset-0 overflow-hidden
     bg-gradient-to-br from-pink-100 via-white to-sky-100 
     dark:from-slate-800 dark:via-slate-900 dark:to-slate-950">
      
      {/* Top bar (make it frosted too) */}
      <div className="backdrop-blur-md bg-white/30 dark:bg-slate-900/30 border-b border-white/20 dark:border-slate-700/30">
          <Topbar onMenuClick={() => uiStore.toggleSidebar()} />
    </div>


      <div className="pt-14 h-full">
        <div className="h-full flex">
          
      {/* Sidebar with frosted glass effect */}
        <div className="backdrop-blur-md bg-white/40 dark:bg-slate-800/30 border-r border-white/20 dark:border-slate-700/30 overflow-y-auto h-full">
           <Sidebar open={sidebarOpen} onClose={() => uiStore.closeSidebar()}>{sidebarContent}</Sidebar>
    </div> 


           {/* Main chat area */}

          <main className="flex-1 min-w-0 h-full flex flex-col 
  backdrop-blur-lg bg-white/20 dark:bg-slate-800/30 
  border border-white/20 dark:border-slate-700/30 
  rounded-xl m-2 p-2 shadow-lg">


            {/* Desktop toggle (always visible) */}
            <div className="hidden sm:flex p-2">
              <button
                className="inline-flex items-center gap-2 rounded-md 
  border border-slate-200 dark:border-slate-700 
  bg-white/70 dark:bg-slate-800/70 
  backdrop-blur-md hover:bg-white/80 dark:hover:bg-slate-700/70 
  px-3 py-1.5 text-sm text-slate-700 dark:text-slate-200 shadow-sm"
                onClick={() => uiStore.toggleSidebar()}
              >
                <span className="text-base">≡</span>
                <span>Toggle sidebar</span>
              </button> 
            </div>
            {children ? children : <Outlet />}
          </main>
        </div>
      </div>
    </div>
  );
}


