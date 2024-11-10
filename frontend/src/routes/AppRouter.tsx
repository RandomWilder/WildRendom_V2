// frontend/src/routes/AppRouter.tsx

import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginForm } from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import UserDashboard from '../components/dashboard/UserDashboard';

// Temporary placeholder for admin dashboard
const AdminDashboard = () => <div>Admin Dashboard Coming Soon</div>;

export const AppRouter = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginForm />} />
      <Route path="/signup" element={<SignupForm />} />
      
      {/* Protected user routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <UserDashboard />
          </ProtectedRoute>
        }
      />
      
      {/* Protected admin routes */}
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute requireAdmin>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />

      {/* Landing page redirect */}
      <Route path="/home" element={<Navigate to="/" replace />} />
      
      {/* Catch all route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};