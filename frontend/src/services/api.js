import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  } else if (!config.headers['Content-Type']) {
    config.headers['Content-Type'] = 'application/json';
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const registerUser = (data) => api.post('/auth/register', data);
export const loginUser = (data) => {
  const params = new URLSearchParams();
  params.append('username', data.email);
  params.append('password', data.password);
  return api.post('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
};

// Users
export const getCurrentUser = () => api.get('/users/me');

// Farms
export const listFarms = () => api.get('/farms');
export const getFarm = (id) => api.get(`/farms/${id}`);
export const createFarm = (data) => api.post('/farms', data);

// Predictions
export const predictDisease = (formData) =>
  api.post('/predictions/disease', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const getPredictionHistory = (page = 1, page_size = 20) =>
  api.get('/predictions/history', { params: { page, page_size } });

export const getPrediction = (id) => api.get(`/predictions/${id}`);
export const getPredictionReport = (id) => api.get(`/predictions/${id}/report`);

// Analysis
export const analyzeWeather = (data) => api.post('/analysis/weather', data);

export const completeAnalysis = (formData) =>
  api.post('/analysis/complete', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const aiReport = (formData) =>
  api.post('/analysis/ai-report', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const predictYield = (data) => api.post('/analysis/yield', data);

// Metadata
export const getSupportedCrops = () => api.get('/metadata/supported-crops');

// Health
export const healthCheck = () => api.get('/health');
