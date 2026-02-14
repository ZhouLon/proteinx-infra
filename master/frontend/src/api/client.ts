import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

client.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
);

export default client;
