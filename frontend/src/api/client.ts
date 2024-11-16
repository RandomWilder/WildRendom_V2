import axios from 'axios';

// Type definitions
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export interface ApiErrorDetails {
  message?: string;
  code?: string;
  details?: unknown;
  status?: number;
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: unknown;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}

interface ApiErrorResponse {
  response?: {
    data?: {
      message?: string;
      code?: string;
      details?: unknown;
    };
    status?: number;
  };
  message?: string;
  request?: unknown;
}

// API Configuration
const API_CONFIG = {
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://production-url.com/api'
    : 'http://localhost:5001',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
} as const;

// Create axios instance
export const apiClient = axios.create(API_CONFIG);

// Request interceptor for debugging in development
if (process.env.NODE_ENV !== 'production') {
  apiClient.interceptors.request.use(
    (config) => {
      console.log('API Request:', {
        url: config.url,
        method: config.method,
        headers: config.headers
      });
      return config;
    },
    (error: Error) => {
      console.error('Request Error:', {
        message: error.message,
        name: error.name
      });
      return Promise.reject(error);
    }
  );

  apiClient.interceptors.response.use(
    (response) => {
      console.log('API Response:', {
        status: response.status,
        data: response.data
      });
      return response;
    },
    (error: unknown) => {
      const err = error as ApiErrorResponse;
      console.error('Response Error:', err?.response || err);
      return Promise.reject(error);
    }
  );
}

// Error handling utility with type safety
export const handleApiError = (error: unknown): ApiError => {
  const err = error as ApiErrorResponse;
  
  if (err?.response) {
    return {
      message: err.response.data?.message || 'Server error occurred',
      status: err.response.status,
      code: err.response.data?.code,
      details: err.response.data?.details
    };
  }

  if (err?.request) {
    return {
      message: 'No response from server. Please check your connection.',
      code: 'NETWORK_ERROR'
    };
  }

  return {
    message: typeof err?.message === 'string' ? err.message : 'Unknown error occurred',
    code: 'REQUEST_ERROR'
  };
};

export default apiClient;