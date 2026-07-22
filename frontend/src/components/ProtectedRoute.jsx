import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="panel loading-panel">Loading your workspace…</div>;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
