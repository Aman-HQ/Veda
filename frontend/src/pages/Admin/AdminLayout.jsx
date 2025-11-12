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
  ChevronRight
} from 'lucide-react';
import { useState } from 'react';

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
          ${sidebarOpen ? 'w-72' : 'w-20'} 
          bg-white dark:bg-slate-900 
          border-r border-slate-200 dark:border-slate-700 
          transition-all duration-300 ease-in-out
          shadow-xl
        `}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          {sidebarOpen && (
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
          )}
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors duration-200"
            aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            {sidebarOpen ? (
              <X size={20} className="text-slate-600 dark:text-slate-400" />
            ) : (
              <Menu size={20} className="text-slate-600 dark:text-slate-400" />
            )}
          </button>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              className={({ isActive }) =>
                `
                  flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
                  ${isActive
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/50'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:shadow-md'
                  }
                `
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon size={20} className={isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400'} />
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
          ))}
        </nav>

        {/* Sidebar Footer - User Info */}
        {sidebarOpen && (
          <div className="p-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                  {user?.name}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                  {user?.email}
                </p>
              </div>
            </div>
          </div>
        )}
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
        {/* Top Bar */}
        <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 shadow-sm">
          <div className="px-4 lg:px-6 py-4">
            <div className="flex items-center justify-between">
              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Menu size={24} className="text-slate-600 dark:text-slate-400" />
              </button>

              {/* Page Title - Hidden on mobile, shown on desktop */}
              <div className="hidden lg:block">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  Veda Admin Dashboard
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                  Manage your healthcare chatbot platform
                </p>
              </div>

              {/* Mobile Logo */}
              <div className="lg:hidden flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Shield className="text-white" size={18} />
                </div>
                <span className="font-bold text-lg bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Admin
                </span>
              </div>

              {/* User Actions */}
              <div className="flex items-center gap-3">
                {/* User Info - Desktop */}
                <div className="hidden md:block text-right">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {user?.name}
                  </p>
                  <div className="flex items-center justify-end gap-2">
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {user?.email}
                    </p>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-sm">
                      Admin
                    </span>
                  </div>
                </div>

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-4 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors duration-200 font-medium"
                  title="Logout"
                >
                  <LogOut size={18} />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 px-6 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
            <p>© 2025 Veda Healthcare. All rights reserved.</p>
            <p>Admin Panel v1.0.0</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
