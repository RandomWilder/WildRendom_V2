// src/admin/components/dashboard/Dashboard.tsx

import { useAdminAuth } from '../../hooks/useAdminAuth';

export const Dashboard = () => {
  const { user } = useAdminAuth();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <div className="text-sm text-gray-500">
          Welcome, {user?.username}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold">Active Raffles</h2>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold">Total Users</h2>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold">Active Prize Pools</h2>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold">Recent Claims</h2>
          <p className="text-3xl font-bold mt-2">0</p>
        </div>
      </div>
    </div>
  );
};