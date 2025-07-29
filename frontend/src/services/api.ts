import axios, { AxiosResponse } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface DashboardMetrics {
  quotes_generated: number;
  quotes_generated_change: number;
  total_revenue: number;
  total_revenue_change: number;
  avg_processing_time: number;
  avg_processing_time_change: number;
  accuracy_rate: number;
  accuracy_rate_change: number;
  quotes_pending: number;
  quotes_approved: number;
  quotes_rejected: number;
  new_clients_this_month: number;
}

export interface Quote {
  id: number;
  quote_number: string;
  client_id: number;
  created_by: number;
  project_name?: string;
  description?: string;
  status: string;
  total_cost: number;
  client_price: number;
  margin: number;
  estimated_delivery_days?: number;
  actual_delivery_days?: number;
  processing_time_minutes?: number;
  ai_confidence_score?: number;
  complexity_level?: string;
  created_at: string;
  updated_at: string;
  quoted_at?: string;
  approved_at?: string;
  client: Client;
  parts: Part[];
  files: QuoteFile[];
}

export interface Client {
  id: number;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  address?: string;
  created_at: string;
  is_active: boolean;
}

export interface Part {
  id: number;
  quote_id: number;
  name: string;
  description?: string;
  quantity: number;
  material_type?: string;
  length?: number;
  width?: number;
  height?: number;
  weight?: number;
  volume?: number;
  machining_operations?: string[];
  estimated_cycle_time?: number;
  actual_cycle_time?: number;
  material_cost: number;
  labor_cost: number;
  overhead_cost: number;
  total_cost: number;
  ai_extracted_features?: any;
  confidence_score?: number;
  created_at: string;
}

export interface QuoteFile {
  id: number;
  quote_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_type: string;
  file_size: number;
  is_processed: boolean;
  processing_status: string;
  extracted_metadata?: any;
  analysis_results?: any;
  created_at: string;
  processed_at?: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

// API methods
export const dashboardAPI = {
  getMetrics: (): Promise<AxiosResponse<DashboardMetrics>> =>
    api.get('/dashboard/metrics'),
  
  getQuoteStatusDistribution: (): Promise<AxiosResponse<any>> =>
    api.get('/dashboard/quote-status-distribution'),
  
  getRevenueByMonth: (): Promise<AxiosResponse<any[]>> =>
    api.get('/dashboard/revenue-by-month'),
  
  getRecentActivity: (): Promise<AxiosResponse<any>> =>
    api.get('/dashboard/recent-activity'),
  
  getTopClients: (): Promise<AxiosResponse<any>> =>
    api.get('/dashboard/top-clients'),
};

export const quotesAPI = {
  list: (params?: any): Promise<AxiosResponse<any>> =>
    api.get('/quotes', { params }),
  
  get: (id: number): Promise<AxiosResponse<Quote>> =>
    api.get(`/quotes/${id}`),
  
  create: (data: any): Promise<AxiosResponse<Quote>> =>
    api.post('/quotes', data),
  
  update: (id: number, data: any): Promise<AxiosResponse<Quote>> =>
    api.put(`/quotes/${id}`, data),
  
  delete: (id: number): Promise<AxiosResponse<any>> =>
    api.delete(`/quotes/${id}`),
  
  analyze: (id: number, data: any): Promise<AxiosResponse<any>> =>
    api.post(`/quotes/${id}/analyze`, data),
  
  getAnalysis: (id: number): Promise<AxiosResponse<any>> =>
    api.get(`/quotes/${id}/analysis`),
  
  approve: (id: number): Promise<AxiosResponse<any>> =>
    api.post(`/quotes/${id}/approve`),
  
  reject: (id: number): Promise<AxiosResponse<any>> =>
    api.post(`/quotes/${id}/reject`),
  
  getParts: (id: number): Promise<AxiosResponse<Part[]>> =>
    api.get(`/quotes/${id}/parts`),
  
  createPart: (id: number, data: any): Promise<AxiosResponse<Part>> =>
    api.post(`/quotes/${id}/parts`, data),
};

export const clientsAPI = {
  list: (params?: any): Promise<AxiosResponse<Client[]>> =>
    api.get('/clients', { params }),
  
  get: (id: number): Promise<AxiosResponse<Client>> =>
    api.get(`/clients/${id}`),
  
  create: (data: any): Promise<AxiosResponse<Client>> =>
    api.post('/clients', data),
  
  update: (id: number, data: any): Promise<AxiosResponse<Client>> =>
    api.put(`/clients/${id}`, data),
  
  delete: (id: number): Promise<AxiosResponse<any>> =>
    api.delete(`/clients/${id}`),
  
  getQuotes: (id: number): Promise<AxiosResponse<Quote[]>> =>
    api.get(`/clients/${id}/quotes`),
  
  getStats: (id: number): Promise<AxiosResponse<any>> =>
    api.get(`/clients/${id}/stats`),
};

export const uploadAPI = {
  uploadFiles: (quoteId: number, files: FileList): Promise<AxiosResponse<any>> => {
    const formData = new FormData();
    formData.append('quote_id', quoteId.toString());
    
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });
    
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  uploadSingleFile: (quoteId: number, file: File): Promise<AxiosResponse<any>> => {
    const formData = new FormData();
    formData.append('quote_id', quoteId.toString());
    formData.append('file', file);
    
    return api.post('/upload/single', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  getQuoteFiles: (quoteId: number): Promise<AxiosResponse<QuoteFile[]>> =>
    api.get(`/upload/${quoteId}/files`),
  
  deleteFile: (fileId: number): Promise<AxiosResponse<any>> =>
    api.delete(`/upload/files/${fileId}`),
  
  downloadFile: (fileId: number): Promise<AxiosResponse<Blob>> =>
    api.get(`/upload/files/${fileId}/download`, {
      responseType: 'blob',
    }),
  
  getSupportedFormats: (): Promise<AxiosResponse<any>> =>
    api.get('/upload/supported-formats'),
  
  processFiles: (quoteId: number, forceReprocess?: boolean): Promise<AxiosResponse<any>> =>
    api.post(`/upload/${quoteId}/process-files`, { force_reprocess: forceReprocess }),
};

export const authAPI = {
  login: (email: string, password: string): Promise<AxiosResponse<any>> =>
    api.post('/auth/login', { email, password }),
  
  register: (data: any): Promise<AxiosResponse<User>> =>
    api.post('/auth/register', data),
  
  getCurrentUser: (): Promise<AxiosResponse<User>> =>
    api.get('/auth/me'),
  
  updateProfile: (data: any): Promise<AxiosResponse<User>> =>
    api.put('/auth/me', data),
  
  refreshToken: (): Promise<AxiosResponse<any>> =>
    api.post('/auth/refresh'),
  
  createAdmin: (): Promise<AxiosResponse<any>> =>
    api.post('/auth/create-admin'),
};

export default api;