// src/components/auth/ProtectedRoute.tsx

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/auth/auth-context';
import { checkAuthToken } from '../../lib/auth/auth-utils';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireAdmin = false 
}) => {
  const { user } = useAuth();
  const location = useLocation();
  const isAuthenticated = checkAuthToken();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !user.isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};