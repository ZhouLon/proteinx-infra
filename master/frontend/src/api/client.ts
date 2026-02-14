import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

client.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

export default client;
