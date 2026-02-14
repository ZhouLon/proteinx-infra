import client from './client';

export interface Job {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  started_at?: string;
  finished_at?: string;
  config: {
    model_type: string;
    epochs: number;
    batch_size: number;
    learning_rate: number;
    dataset_path: string;
  };
  node_id?: string;
}

export interface CreateJobParams {
  name: string;
  config: Job['config'];
}

export const createJob = async (params: CreateJobParams): Promise<Job> => {
  const response = await client.post<Job>('/jobs', params);
  return response.data;
};

export const getJobs = async (): Promise<Job[]> => {
  const response = await client.get<Job[]>('/jobs');
  return response.data;
};

export const getJobDetail = async (jobId: string): Promise<Job> => {
  const response = await client.get<Job>(`/jobs/${jobId}`);
  return response.data;
};

export const getJobLogs = async (jobId: string): Promise<string> => {
  const response = await client.get<string>(`/jobs/${jobId}/logs`);
  return response.data;
};

export const cancelJob = async (jobId: string) => {
  await client.post(`/jobs/${jobId}/cancel`);
};

export const getArtifactDownloadUrl = (jobId: string) => {
  return `/api/jobs/${jobId}/artifacts/download`;
};
