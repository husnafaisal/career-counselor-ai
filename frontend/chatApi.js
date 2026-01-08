import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const createSession = async () => {
  try {
    const response = await api.post('/api/sessions');
    return response.data;
  } catch (error) {
    throw new Error('Failed to create session');
  }
};

export const sendMessage = async (sessionId, message) => {
  try {
    const response = await api.post('/api/chat', {
      session_id: sessionId,
      message: message,
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to send message');
  }
};

export const getSessionState = async (sessionId) => {
  try {
    const response = await api.get(`/api/sessions/${sessionId}/state`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to get session state');
  }
};

export const getConversationHistory = async (sessionId) => {
  try {
    const response = await api.get(`/api/sessions/${sessionId}/history`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to get conversation history');
  }
};

export const resetSession = async (sessionId) => {
  try {
    const response = await api.post(`/api/sessions/${sessionId}/reset`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to reset session');
  }
};

export const getAnalytics = async () => {
  try {
    const response = await api.get('/api/analytics/dashboard');
    return response.data;
  } catch (error) {
    throw new Error('Failed to get analytics');
  }
};

export default api;