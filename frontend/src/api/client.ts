import axios from 'axios';

// API Configuration
const API_CONFIG = {
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://production-url.com/api'
    : '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

// Create axios instance
export const apiClient = axios.create(API_CONFIG);

// Error type definition
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

// Response type for paginated data
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
      details?: any;
    };
    status?: number;
  };
  message?: string;
  request?: any;
}

// Error handling utility
export const handleApiError = (rawError: any): ApiError => {
  const error = rawError as ApiErrorResponse;
  
  if (error.response) {
    return {
      message: error.response.data?.message || 'Server error occurred',
      status: error.response.status,
      code: error.response.data?.code,
      details: error.response.data?.details
    };
  }

  if (error.request) {
    return {
      message: 'No response from server. Please check your connection.',
      code: 'NETWORK_ERROR'
    };
  }

  return {
    message: error.message || 'Unknown error occurred',
    code: 'REQUEST_ERROR'
  };
};

export default apiClient;