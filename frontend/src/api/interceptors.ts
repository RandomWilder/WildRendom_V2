import apiClient from './client';

// Custom request interface
interface RequestConfig {
  headers: Record<string, string>;
  _retry?: boolean;
}

// Get token from storage
const getAuthToken = (): string | null => {
  try {
    const authData = localStorage.getItem('auth_token');
    if (!authData) return null;
    const { token } = JSON.parse(authData);
    return token;
  } catch {
    return null;
  }
};

// Request interceptor
const requestInterceptor = (config: any): any => {
  const token = getAuthToken();
  
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
};

// Response interceptor
const responseInterceptor = (response: any): any => {
  return response;
};

// Error interceptor
const errorInterceptor = (error: any): Promise<never> => {
  const config = error.config as RequestConfig;
  
  if (error.response?.status === 401 && !config._retry) {
    config._retry = true;
    
    // Clear auth state
    localStorage.removeItem('auth_token');
    
    // Redirect to login
    window.location.href = '/login';
  }

  return Promise.reject(error);
};

// Add interceptors to client
apiClient.interceptors.request.use(requestInterceptor);
apiClient.interceptors.response.use(responseInterceptor, errorInterceptor);

export default apiClient;