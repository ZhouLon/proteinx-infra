import client from './client';

export interface LoginParams {
  username: string;
  password?: string;
  token?: string;
}

export interface RegisterParams {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    role: string;
  };
}

export const login = async (params: LoginParams): Promise<LoginResponse> => {
  const response = await client.post<LoginResponse>('/auth/token', params);
  return response.data;
};

export const existsUser = async (): Promise<{ exists: boolean }> => {
  const response = await client.get<{ exists: boolean }>('/auth/exists');
  return response.data;
};

export const register = async (params: RegisterParams): Promise<{ ok: boolean }> => {
  const response = await client.post<{ ok: boolean }>('/auth/register', params);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await client.get('/auth/me');
  return response.data;
};

export const refreshToken = async (refreshToken: string) => {
  const response = await client.post('/auth/refresh', { refresh_token: refreshToken });
  return response.data;
};
