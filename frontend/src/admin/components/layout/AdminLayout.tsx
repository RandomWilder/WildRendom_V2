import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from "lucide-react";
import { useAdminAuth } from '../../hooks/useAdminAuth';
import AdminSidebar from './AdminSidebar';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export const AdminLayout = ({ children }: AdminLayoutProps) => {
  const { isAuthenticated, isAdmin, isLoading, user } = useAdminAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAuthenticated || !isAdmin || !user) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        <AdminSidebar />
        <main className="flex-1 p-6 overflow-auto">
          <div className="container mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};