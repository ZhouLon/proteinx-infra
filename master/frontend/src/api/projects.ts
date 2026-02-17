import client from './client';

export interface ProjectInfo {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  models_count: number;
  pinned_at?: string | null;
}

export const listProjects = async (): Promise<ProjectInfo[]> => {
  const res = await client.get<ProjectInfo[]>('/projects');
  return res.data;
};

export const createProject = async (name: string, description: string): Promise<ProjectInfo> => {
  const res = await client.post<ProjectInfo>('/projects', { name, description });
  return res.data;
};

export const pinProject = async (pid: string): Promise<ProjectInfo> => {
  const res = await client.post<ProjectInfo>(`/projects/${pid}/pin`);
  return res.data;
};

export const unpinProject = async (pid: string): Promise<ProjectInfo> => {
  const res = await client.post<ProjectInfo>(`/projects/${pid}/unpin`);
  return res.data;
};
