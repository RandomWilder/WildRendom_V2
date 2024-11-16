// src/admin/hooks/useAdminAuth.ts

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { UserResponse } from '../../api/endpoints/auth';
import { useAdminStore } from '../stores/adminAuthStore';

// Extend UserResponse type to include admin property
type AdminUserResponse = UserResponse & { isAdmin: boolean };

interface AdminAuthResponse {
  user: AdminUserResponse;
  token: string;
}

export const useAdminAuth = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const { user, token, setAuth, clearAuth } = useAdminStore();

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      console.log('Attempting admin login...', { username });
      
      const response = await apiClient.post<AdminAuthResponse>('/api/admin/login', {
        username,
        password
      });

      console.log('Login response:', response.data);

      const { user, token } = response.data;
      
      if (!user.isAdmin) {
        throw new Error('Unauthorized: Admin access required');
      }

      localStorage.setItem('admin_token', token);
      setAuth(user, token);
      navigate('/admin/dashboard');
      
    } catch (error: any) {
      console.error('Login error:', error.response?.data || error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      } else {
        throw new Error('Invalid admin credentials');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const checkAuthStatus = useCallback(async () => {
    try {
      const storedToken = localStorage.getItem('admin_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      if (apiClient.defaults.headers.common) {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
      }
      
      const response = await apiClient.get<{user: AdminUserResponse}>('/api/admin/verify', {
        headers: { Authorization: `Bearer ${storedToken}` }
      });

      if (!response.data.user.isAdmin) {
        throw new Error('Unauthorized access');
      }

      setAuth(response.data.user, storedToken);
    } catch (error) {
      console.error('Auth check failed:', error);
      clearAuth();
      localStorage.removeItem('admin_token');
      if (apiClient.defaults.headers.common) {
        delete apiClient.defaults.headers.common['Authorization'];
      }
    } finally {
      setIsLoading(false);
    }
  }, [setAuth, clearAuth]);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const logout = useCallback(() => {
    localStorage.removeItem('admin_token');
    if (apiClient.defaults.headers.common) {
      delete apiClient.defaults.headers.common['Authorization'];
    }
    clearAuth();
    navigate('/admin/login');
  }, [clearAuth, navigate]);

  return {
    isAuthenticated: !!token && !!user?.isAdmin,
    isAdmin: !!user?.isAdmin,
    isLoading,
    login,
    logout,
    user
  };
};