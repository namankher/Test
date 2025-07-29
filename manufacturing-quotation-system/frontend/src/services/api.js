import axios from 'axios';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Quote Management APIs
export const createQuote = (quoteData) => {
  const formData = new FormData();
  formData.append('client_name', quoteData.clientName);
  formData.append('client_email', quoteData.clientEmail);
  if (quoteData.projectDescription) {
    formData.append('project_description', quoteData.projectDescription);
  }
  
  return api.post('/upload/create-quote', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getQuoteById = (quoteId) => {
  return api.get(`/quotation/quote/${quoteId}`);
};

export const getQuotesDashboard = (params = {}) => {
  return api.get('/quotation/quotes/dashboard', { params });
};

export const deleteQuote = (quoteId) => {
  return api.delete(`/quotation/quote/${quoteId}`);
};

// File Upload APIs
export const uploadFiles = (quoteId, formData) => {
  return api.post(`/upload/files/${quoteId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getQuoteFiles = (quoteId) => {
  return api.get(`/upload/quote/${quoteId}/files`);
};

export const deleteFile = (fileId) => {
  return api.delete(`/upload/files/${fileId}`);
};

export const getSupportedFormats = () => {
  return api.get('/upload/supported-formats');
};

// Analysis APIs
export const startAnalysis = (quoteId) => {
  return api.post(`/analysis/start/${quoteId}`);
};

export const getAnalysisStatus = (quoteId) => {
  return api.get(`/analysis/status/${quoteId}`);
};

export const getAnalysisResults = (quoteId) => {
  return api.get(`/analysis/results/${quoteId}`);
};

export const updatePartAnalysis = (quoteId, partId, partData) => {
  return api.put(`/analysis/results/${quoteId}/part/${partId}`, partData);
};

export const deletePartAnalysis = (quoteId, partId) => {
  return api.delete(`/analysis/results/${quoteId}/part/${partId}`);
};

export const reanalyzeQuote = (quoteId) => {
  return api.post(`/analysis/reanalyze/${quoteId}`);
};

// Quotation APIs
export const calculateCosts = (quoteId, quotationInput) => {
  return api.post(`/quotation/calculate/${quoteId}`, quotationInput);
};

export const getCostBreakdown = (quoteId) => {
  return api.get(`/quotation/costs/${quoteId}`);
};

export const approveQuote = (quoteId) => {
  return api.post(`/quotation/approve/${quoteId}`);
};

export const generateClientQuote = (quoteId, includeBreakdown = false) => {
  return api.post(`/quotation/generate-client-quote/${quoteId}`, null, {
    params: { include_breakdown: includeBreakdown },
  });
};

export const sendQuoteToClient = (quoteId) => {
  return api.post(`/quotation/send-to-client/${quoteId}`);
};

export const getInternalQuoteRecord = (quoteId) => {
  return api.get(`/quotation/internal-record/${quoteId}`);
};

// Feedback APIs
export const submitFeedback = (quoteId, feedbackData) => {
  return api.post(`/feedback/submit/${quoteId}`, feedbackData);
};

export const getQuoteFeedback = (quoteId) => {
  return api.get(`/feedback/quote/${quoteId}`);
};

export const getAccuracyAnalytics = (limit = 100) => {
  return api.get('/feedback/analytics/accuracy', { params: { limit } });
};

export const getTrainingData = () => {
  return api.get('/feedback/training-data');
};

export const triggerModelRetraining = () => {
  return api.post('/feedback/retrain-model');
};

// Utility APIs
export const getHealthCheck = () => {
  return api.get('/health');
};

export default api;