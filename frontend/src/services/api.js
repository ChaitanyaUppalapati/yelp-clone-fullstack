// services/api.js — Axios instance with JWT interceptor
import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Base URL for serving static media (avatars, review photos). When API_BASE_URL is
// absolute we reuse it; when it's relative (e.g. "/api" behind a proxy) we fall
// back to the page origin.
export const MEDIA_BASE_URL = API_BASE_URL.startsWith('http')
  ? API_BASE_URL
  : window.location.origin;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
