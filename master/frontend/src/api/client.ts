import axios from 'axios';
import type { AxiosRequestConfig } from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

client.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token');
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any)['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original: AxiosRequestConfig & { _retry?: boolean } = error.config || {};
    if (error.response && error.response.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = sessionStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const res = await client.post('/auth/refresh', { refresh_token: refresh });
          const newAccess = res.data?.access_token;
          if (newAccess) {
            sessionStorage.setItem('access_token', newAccess);
            original.headers = original.headers || {};
            (original.headers as any)['Authorization'] = `Bearer ${newAccess}`;
            return client.request(original);
          }
        } catch {
          // fallthrough to redirect
        }
      }
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default client;
