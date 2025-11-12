
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthAction from './components/AuthAction.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import ChatPage from './pages/ChatPage.jsx';
import OAuthCallback from './pages/OAuthCallback.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import ResendVerification from './components/ResendVerification.jsx';
import ProtectedRoute from './routes/ProtectedRoute.jsx';
import AuthLayout from './components/Layout/AuthLayout.jsx';

// Admin imports
import AdminLayout from './pages/Admin/AdminLayout.jsx';
import AdminDashboard from './pages/Admin/Dashboard.jsx';
import AdminUsers from './pages/Admin/Users.jsx';
import AdminModeration from './pages/Admin/Moderation.jsx';
import AdminMetrics from './pages/Admin/Metrics.jsx';
import AdminSystemHealth from './pages/Admin/SystemHealth.jsx';
import useAuth from './hooks/useAuth.js';

// Admin Route Protection Component
function AdminRoute({ children }) {
  const { user, isAuthenticated, loading } = useAuth();
  
  // Wait for authentication check to complete
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (user?.role !== 'admin') {
    return <Navigate to="/chat" replace />;
  }
  
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthLayout><Login /></AuthLayout>} />
      <Route path="/register" element={<AuthLayout><Register /></AuthLayout>} />
      <Route path="/forgot-password" element={<AuthLayout><ForgotPassword /></AuthLayout>} />
      <Route path="/resend-verification" element={<ResendVerification />} />
      <Route path="/auth-action" element={<AuthAction />} />
      <Route path="/oauth/callback" element={<OAuthCallback />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/chat" element={<ChatPage />} />
      </Route>
      
      {/* Admin routes */}
      <Route path="/admin" element={
        <AdminRoute>
          <AdminLayout />
        </AdminRoute>
      }>
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<AdminUsers />} />
        <Route path="moderation" element={<AdminModeration />} />
        <Route path="metrics" element={<AdminMetrics />} />
        <Route path="health" element={<AdminSystemHealth />} />
      </Route>
      
      <Route path="/" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}

export default App;
