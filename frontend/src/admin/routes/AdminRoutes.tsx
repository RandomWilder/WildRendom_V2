import { Routes, Route, Navigate } from 'react-router-dom';
import { AdminLayout } from '../components/layout/AdminLayout';
import { LoginPage } from '../components/auth/LoginPage';
import { Dashboard } from '../components/dashboard/Dashboard';
import PrizeManagement from '../components/prizes/PrizeManagement';

export const AdminRoutes = () => {
  return (
    <Routes>
      {/* Public admin routes */}
      <Route path="login" element={<LoginPage />} />

      {/* Protected admin routes - nested under /admin */}
      <Route path="/*" element={
        <AdminLayout>
          <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="prizes/*" element={<PrizeManagement />} />
            {/* Add other management routes as they are developed */}
            <Route path="raffles/*" element={<div>Raffle Management (Coming Soon)</div>} />
            <Route path="users/*" element={<div>User Management (Coming Soon)</div>} />
            <Route path="bonuses/*" element={<div>Bonus Management (Coming Soon)</div>} />
            <Route path="analytics/*" element={<div>Analytics Dashboard (Coming Soon)</div>} />
            <Route path="settings/*" element={<div>System Settings (Coming Soon)</div>} />
          </Routes>
        </AdminLayout>
      } />
    </Routes>
  );
};