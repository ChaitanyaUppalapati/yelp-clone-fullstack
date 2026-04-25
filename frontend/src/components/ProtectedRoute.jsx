// components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';

export default function ProtectedRoute({ children, ownerOnly = false }) {
  const { isAuthenticated, user, loading } = useSelector((state) => state.auth);
  const isOwner = user?.role === 'owner';

  if (loading) {
    return (
      <div className="loading-center page">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (ownerOnly && !isOwner) {
    return <Navigate to="/" replace />;
  }

  return children;
}
