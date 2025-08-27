import { Navigate, Outlet } from 'react-router-dom';
import authStore from '../stores/authStore.js';

export default function ProtectedRoute() {
  const isAuthed = Boolean(authStore.getAccessToken());
  if (!isAuthed) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}


