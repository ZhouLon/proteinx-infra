import axios from 'axios';

// Create axios instance with base URL
const client = axios.create({
  baseURL: '/api', // Proxy will handle this in dev, or Nginx in prod
  timeout: 10000,
});

// Interceptor for handling errors or token injection (later)
client.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

export default client;
