import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';
import { 
  LayoutDashboard, 
  Users, 
  Shield, 
  LogOut,
  Menu,
  X,
  Activity,
  Heart,
  ChevronRight,
  ChevronLeft,
  User,
  Settings,
  MessageCircle
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

// Custom Tooltip Component
function Tooltip({ children, text, show }) {
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef(null);

  const handleMouseEnter = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPosition({
        top: rect.top + rect.height / 2,
        left: rect.right + 8
      });
    }
  };

  if (!show || !text) return children;
  
  return (
    <div 
      ref={triggerRef}
      onMouseEnter={handleMouseEnter}
      className="relative group/tooltip"
    >
      {children}
      <div 
        className="fixed opacity-0 group-hover/tooltip:opacity-100 pointer-events-none transition-opacity duration-100 -translate-y-1/2"
        style={{ top: `${position.top}px`, left: `${position.left}px`, zIndex: 99999 }}
      >
        <div className="bg-slate-900 dark:bg-slate-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium shadow-xl whitespace-nowrap">
          {text}
          {/* Arrow */}
          <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-slate-900 dark:border-r-slate-700"></div>
        </div>
      </div>
    </div>
  );
}

export default function AdminLayout() {
  const { user, logout, loading } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  // Close user menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    { 
      path: '/admin', 
      label: 'Dashboard', 
      icon: LayoutDashboard, 
      exact: true,
      description: 'Overview & Statistics'
    },
    { 
      path: '/admin/users', 
      label: 'Users', 
      icon: Users,
      description: 'User Management'
    },
    { 
      path: '/admin/moderation', 
      label: 'Moderation', 
      icon: Shield,
      description: 'Content Filtering'
    },
    { 
      path: '/admin/metrics', 
      label: 'Metrics', 
      icon: Activity,
      description: 'Real-time Analytics'
    },
    { 
      path: '/admin/health', 
      label: 'System Health', 
      icon: Heart,
      description: 'Component Status'
    },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Sidebar - Desktop */}
      <aside 
        className={`
          hidden lg:flex flex-col
          ${sidebarOpen ? 'w-72' : 'w-24'} 
          bg-white dark:bg-slate-900 
          border-r border-slate-200 dark:border-slate-700 
          transition-all duration-300 ease-in-out
          shadow-xl
        `}
      >
        {/* Sidebar Header */}
        <div className={`flex items-center ${sidebarOpen ? 'justify-between px-6 py-6 border-b border-slate-200 dark:border-slate-700' : 'justify-center py-6'} border-b border-slate-200 dark:border-slate-700`}>
          {sidebarOpen ? (
            <>
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <button
                onClick={() => setSidebarOpen(false)}
                className="w-12 h-12 p-0 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg flex-shrink-0 relative group hover:shadow-xl transition-shadow duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 border-0"
                style={{ borderRadius: '50%' }}
                aria-label="Collapse sidebar"
              >
                <Shield className="text-white absolute group-hover:opacity-0 transition-opacity duration-200" size={22} />
                <ChevronLeft className="text-white absolute opacity-0 group-hover:opacity-100 transition-opacity duration-200" size={22} />
              </button>
              <div className="min-w-0 ml-2">
                <h1 className="text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Admin Panel
                </h1>
              </div>
            </div>
            </>
          ) : (
            <button
              onClick={() => setSidebarOpen(true)}
              className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-0 rounded-full bg-transparent p-0 m-0 border-0 bg-transparent hover:scale-105 transition-transform"
              aria-label="Expand sidebar"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow cursor-pointer">
                <Shield className="text-white" size={24} />
              </div>
            </button>
          )}
        </div>
        
        {/* Navigation */}
        <nav className={`flex-1 p-4 overflow-y-auto ${!sidebarOpen ? 'space-y-6' : 'space-y-2'}`}>
          {navItems.map((item) => (
            <Tooltip key={item.path} text={item.label} show={!sidebarOpen}>
              <NavLink
                to={item.path}
                end={item.exact}
                className={({ isActive }) =>
                  `
                    relative flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2
                    ${isActive
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md'
                      : `text-slate-700 dark:text-slate-300 ${sidebarOpen ? 'hover:bg-slate-50 dark:hover:bg-slate-800/50' : ''}`
                    }
                  `
                }
              >
                {({ isActive }) => (
                  <>
                    {/* Left Border Accent */}
                    <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl transition-all duration-200 ${
                      isActive 
                        ? 'bg-white' 
                        : 'bg-transparent group-hover:bg-indigo-500'
                    }`} />
                    
                    <item.icon size={20} className={isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors'} />
                    {sidebarOpen && (
                      <div className="flex-1 min-w-0">
                        <span className="font-semibold text-sm block truncate">{item.label}</span>
                        <span className={`text-xs block truncate ${isActive ? 'text-indigo-100' : 'text-slate-500 dark:text-slate-400'}`}>
                          {item.description}
                        </span>
                      </div>
                    )}
                    {sidebarOpen && isActive && (
                      <ChevronRight size={16} className="text-white flex-shrink-0" />
                    )}
                  </>
                )}
              </NavLink>
            </Tooltip>
          ))}
        </nav>

        {/* Sidebar Footer - User Info */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-700 relative" ref={userMenuRef}>
          {loading ? (
            <div className={`flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl animate-pulse ${!sidebarOpen && 'justify-center'}`}>
              <div className="w-10 h-10 bg-slate-300 dark:bg-slate-700 rounded-full" />
              {sidebarOpen && (
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-slate-300 dark:bg-slate-700 rounded w-24" />
                  <div className="h-2 bg-slate-300 dark:bg-slate-700 rounded w-32" />
                </div>
              )}
            </div>
          ) : (
            <>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className={`w-full flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${!sidebarOpen && 'justify-center'}`}
              >
                <div className="relative">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg animate-pulse" style={{ animationDuration: '3s' }}>
                    {user?.name?.charAt(0).toUpperCase()}
                  </div>
                  <div className="absolute inset-0 rounded-full bg-indigo-400 opacity-0 group-hover:opacity-20 transition-opacity blur-md" />
                </div>
                {sidebarOpen && (
                  <>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                        {user?.name}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                        {user?.email}
                      </p>
                    </div>
                    <ChevronRight 
                      size={16} 
                      className={`text-slate-400 transition-transform duration-200 ${userMenuOpen ? 'rotate-90' : ''}`}
                    />
                  </>
                )}
              </button>

              {/* User Dropdown Menu */}
              {userMenuOpen && (
                <div className={`absolute bottom-full mb-2 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-200 z-50 ${
                  sidebarOpen ? 'left-4 right-4' : 'left-4 w-56'
                }`}>
                  <div className="p-2 space-y-1">
                    {/* User Info Header - Only show when sidebar is collapsed */}
                    {!sidebarOpen && (
                      <>
                        <div className="px-3 py-2 border-b border-slate-200 dark:border-slate-700">
                          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                            {user?.name}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {user?.email}
                          </p>
                        </div>
                      </>
                    )}

                    {/* Profile Option */}
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        navigate('/profile');
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                    >
                      <User size={18} className="text-slate-500 dark:text-slate-400" />
                      <span className="text-sm font-medium">Profile</span>
                    </button>

                    {/* Chat Page Option */}
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        navigate('/chat');
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                    >
                      <MessageCircle size={18} className="text-slate-500 dark:text-slate-400" />
                      <span className="text-sm font-medium">Chat Page</span>
                    </button>

                    {/* Settings Option */}
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        navigate('/settings');
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                    >
                      <Settings size={18} className="text-slate-500 dark:text-slate-400" />
                      <span className="text-sm font-medium">Settings</span>
                    </button>

                    {/* Divider */}
                    <div className="my-1 border-t border-slate-200 dark:border-slate-700" />

                    {/* Logout Option */}
                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        handleLogout();
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
                    >
                      <LogOut size={18} />
                      <span className="text-sm font-medium">Log out</span>
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside 
        className={`
          fixed top-0 left-0 bottom-0 w-72 bg-white dark:bg-slate-900 z-50 lg:hidden
          transform transition-transform duration-300 ease-in-out shadow-2xl
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Mobile Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <Shield className="text-white" size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Admin Panel
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Veda Healthcare</p>
            </div>
          </div>
          <button 
            onClick={() => setMobileMenuOpen(false)}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X size={20} className="text-slate-600 dark:text-slate-400" />
          </button>
        </div>

        {/* Mobile Navigation */}
        <nav className="p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                `
                  flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                  ${isActive
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }
                `
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={20} />
                  <div className="flex-1">
                    <span className="font-semibold text-sm block">{item.label}</span>
                    <span className={`text-xs block ${isActive ? 'text-indigo-100' : 'text-slate-500 dark:text-slate-400'}`}>
                      {item.description}
                    </span>
                  </div>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Menu Button - Floating */}
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="lg:hidden fixed top-4 left-4 z-40 p-2 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors shadow-lg border border-slate-200 dark:border-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
        >
          <Menu size={24} className="text-slate-600 dark:text-slate-400" />
        </button>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-3 sm:p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
