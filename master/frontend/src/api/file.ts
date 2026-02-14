import client from './client';

export interface FileInfo {
  name: string;
  path: string;
  size: number;
  updated_at: string;
  type: 'file' | 'directory';
}

export const listFiles = async (path: string = '/'): Promise<FileInfo[]> => {
  const response = await client.get<FileInfo[]>('/files/list', { params: { path } });
  return response.data;
};

export const uploadFile = async (file: File, path: string = '/') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('path', path);

  await client.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const deleteFile = async (path: string) => {
  await client.delete('/files', { params: { path } });
};

export const previewFile = async (path: string): Promise<string> => {
  const response = await client.get<string>('/files/preview', { params: { path } });
  return response.data;
};
