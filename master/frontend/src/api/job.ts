import client from './client';

export interface TrainingParams {
  name: string;
  config: {
    model_type: string;
    dataset_path: string;
    epochs: number;
    learning_rate: number;
    batch_size?: number;
  };
}

export const createJob = async (pid: string, params: TrainingParams): Promise<{ id: string }> => {
  const res = await client.post<{ id: string }>(`/projects/${pid}/jobs`, params);
  return res.data;
};

export const listJobs = async (pid: string, status?: string): Promise<{ items: any[]; total: number }> => {
  const res = await client.get<{ items: any[]; total: number }>(`/projects/${pid}/jobs`, { params: { status } });
  return res.data;
};

export const getJobDetail = async (pid: string, jid: string) => {
  const res = await client.get<any>(`/projects/${pid}/jobs/${jid}`);
  return res.data;
};

export const getJobLogs = async (pid: string, jid: string): Promise<{ logs: string }> => {
  const res = await client.get<{ logs: string }>(`/projects/${pid}/jobs/${jid}/logs`);
  return res.data;
};

export const cancelJob = async (pid: string, jid: string): Promise<{ ok: boolean }> => {
  const res = await client.post<{ ok: boolean }>(`/projects/${pid}/jobs/${jid}/cancel`);
  return res.data;
};
