import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const instance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorEnvelope = error.response?.data || {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: error.message || 'Failed to connect to backend server',
        details: [],
      },
    };
    return Promise.reject(errorEnvelope);
  }
);

export const apiClient = {
  get: async <T = any>(url: string, config?: any): Promise<T> => {
    return instance.get(url, config) as unknown as Promise<T>;
  },
  post: async <T = any>(url: string, data?: any, config?: any): Promise<T> => {
    return instance.post(url, data, config) as unknown as Promise<T>;
  },
  put: async <T = any>(url: string, data?: any, config?: any): Promise<T> => {
    return instance.put(url, data, config) as unknown as Promise<T>;
  },
  patch: async <T = any>(url: string, data?: any, config?: any): Promise<T> => {
    return instance.patch(url, data, config) as unknown as Promise<T>;
  },
  delete: async <T = any>(url: string, config?: any): Promise<T> => {
    return instance.delete(url, config) as unknown as Promise<T>;
  },
  /**
   * Raw GET — bypasses the response interceptor so callers can access
   * both response.data and response.headers (e.g. for file downloads).
   */
  getRaw: async (url: string, config?: any) => {
    return axios.get(`${API_BASE_URL}${url}`, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000,
      ...config,
    });
  },
};

export interface APIResponse<T> {
  success: boolean;
  status?: string;
  data?: T;
  error?: {
    code: string;
    message: string;
    details: string[];
  };
}
