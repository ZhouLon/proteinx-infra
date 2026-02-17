import client from './client';

export const listRecycleProjects = async (): Promise<{ items: Array<{ id: string; name: string; deleted_at: string }> }> => {
  const res = await client.get('/recycle/projects');
  return res.data;
};

export const restoreRecycleProject = async (pid: string): Promise<{ ok?: boolean }> => {
  const res = await client.post(`/recycle/projects/${pid}/restore`);
  return res.data;
};

export const deleteRecycleProject = async (pid: string): Promise<{ ok?: boolean }> => {
  const res = await client.delete(`/recycle/projects/${pid}`);
  return res.data;
};
