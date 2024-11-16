import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Gift,
  Ticket,
  Users,
  Coins,
  ChevronLeft,
  ChevronRight,
  Settings,
  PieChart
} from 'lucide-react';

const MenuItem = ({ icon: Icon, text, to, collapsed }) => {
  const location = useLocation();
  const isActive = location.pathname.startsWith(to);

  return (
    <NavLink
      to={to}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors hover:bg-gray-100 ${
        isActive ? 'bg-gray-100 text-primary' : 'text-gray-600'
      }`}
    >
      <Icon className="w-5 h-5" />
      {!collapsed && <span className="text-sm font-medium">{text}</span>}
    </NavLink>
  );
};

const AdminSidebar = () => {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { icon: LayoutDashboard, text: 'Dashboard', to: '/admin/dashboard' },
    { icon: Gift, text: 'Prizes & Pools', to: '/admin/prizes' },
    { icon: Ticket, text: 'Raffles', to: '/admin/raffles' },
    { icon: Users, text: 'Users', to: '/admin/users' },
    { icon: Coins, text: 'Bonuses', to: '/admin/bonuses' },
    { icon: PieChart, text: 'Analytics', to: '/admin/analytics' },
    { icon: Settings, text: 'Settings', to: '/admin/settings' },
  ];

  return (
    <div 
      className={`bg-white border-r border-gray-200 h-screen transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-4 border-b border-gray-200">
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
          {!collapsed && <span className="text-lg font-semibold">Admin</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-lg hover:bg-gray-100"
          >
            {collapsed ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
      <nav className="p-2 space-y-1">
        {menuItems.map((item) => (
          <MenuItem
            key={item.to}
            icon={item.icon}
            text={item.text}
            to={item.to}
            collapsed={collapsed}
          />
        ))}
      </nav>
    </div>
  );
};

export default AdminSidebar;