// src/admin/stores/adminAuthStore.ts

import { create } from 'zustand';
import { UserResponse } from '../../api/endpoints/auth';

interface AdminState {
  user: UserResponse | null;
  token: string | null;
  setAuth: (user: UserResponse, token: string) => void;
  clearAuth: () => void;
}

export const useAdminStore = create<AdminState>((set) => ({
  user: null,
  token: null,
  setAuth: (user, token) => set({ user, token }),
  clearAuth: () => set({ user: null, token: null }),
}));