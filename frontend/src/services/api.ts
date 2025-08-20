import axios from 'axios';
import { MigrationJob, MigrationRequest, DashboardStats, SystemConfig, UserRecord } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:12001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
    return Promise.reject(error);
  }
);

export const apiService = {
  // System endpoints
  getSupportedSystems: async (): Promise<string[]> => {
    const response = await api.get('/systems');
    return response.data;
  },

  getSystemConfig: async (systemType: string): Promise<SystemConfig> => {
    const response = await api.get(`/systems/${systemType}/config`);
    return response.data;
  },

  updateSystemConfig: async (systemType: string, config: SystemConfig): Promise<SystemConfig> => {
    const response = await api.post(`/systems/${systemType}/config`, config);
    return response.data;
  },

  getSystemUsers: async (systemType: string, limit = 100, offset = 0): Promise<UserRecord[]> => {
    const response = await api.get(`/systems/${systemType}/users`, {
      params: { limit, offset }
    });
    return response.data;
  },

  getSystemUserCount: async (systemType: string): Promise<{ count: number }> => {
    const response = await api.get(`/systems/${systemType}/users/count`);
    return response.data;
  },

  // Migration endpoints
  createMigrationJob: async (request: MigrationRequest): Promise<MigrationJob> => {
    const response = await api.post('/migrations', request);
    return response.data;
  },

  getMigrationJobs: async (): Promise<MigrationJob[]> => {
    const response = await api.get('/migrations');
    return response.data;
  },

  getMigrationJob: async (jobId: string): Promise<MigrationJob> => {
    const response = await api.get(`/migrations/${jobId}`);
    return response.data;
  },

  pauseMigrationJob: async (jobId: string): Promise<{ message: string; job_id: string }> => {
    const response = await api.post(`/migrations/${jobId}/pause`);
    return response.data;
  },

  resumeMigrationJob: async (jobId: string): Promise<{ message: string; job_id: string }> => {
    const response = await api.post(`/migrations/${jobId}/resume`);
    return response.data;
  },

  deleteMigrationJob: async (jobId: string): Promise<{ message: string; job_id: string }> => {
    const response = await api.delete(`/migrations/${jobId}`);
    return response.data;
  },

  // Dashboard endpoints
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ message: string; version: string }> => {
    const response = await api.get('/');
    return response.data;
  },
};

export default apiService;