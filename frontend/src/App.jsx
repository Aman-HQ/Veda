
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import ChatPage from './pages/ChatPage.jsx';
import ProtectedRoute from './routes/ProtectedRoute.jsx';
import AuthLayout from './components/Layout/AuthLayout.jsx';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthLayout><Login /></AuthLayout>} />
      <Route path="/register" element={<AuthLayout><Register /></AuthLayout>} />
      <Route element={<ProtectedRoute />}>
        <Route path="/chat" element={<ChatPage />} />
      </Route>
      <Route path="/" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}

export default App;
