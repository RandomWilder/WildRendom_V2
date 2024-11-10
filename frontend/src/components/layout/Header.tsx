// src/components/layout/Header.tsx

import { Link } from 'react-router-dom';
import { useAuth } from '../../lib/auth/auth-context';

export const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow">
      <nav className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link to="/" className="text-xl font-bold text-indigo-600">
            Wild Random
          </Link>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                {user.isAdmin && (
                  <Link
                    to="/admin"
                    className="text-gray-600 hover:text-gray-900"
                  >
                    Admin Panel
                  </Link>
                )}
                <button
                  onClick={logout}
                  className="text-gray-600 hover:text-gray-900"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="text-gray-600 hover:text-gray-900"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
};