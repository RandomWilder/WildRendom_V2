import apiClient from '../client';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  siteCredits: number;
  isAdmin: boolean;
  isActive: boolean;
  isVerified: boolean;
}

export interface AuthResponse {
  user: UserResponse;
  token: string;
}

const authEndpoints = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/users/login', credentials);
    return response.data;
  },

  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/users/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>('/users/me');
    return response.data;
  },

  updateProfile: async (userId: number, data: Partial<UserResponse>): Promise<UserResponse> => {
    const response = await apiClient.put<UserResponse>(`/users/${userId}`, data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    localStorage.removeItem('auth_token');
  }
};

export default authEndpoints;