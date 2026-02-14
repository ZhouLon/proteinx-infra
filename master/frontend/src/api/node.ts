import client from './client';

export interface NodeInfo {
  id: string;
  ip: string;
  hostname: string;
  status: 'idle' | 'busy' | 'offline';
  resources: {
    cpu_usage: number;
    memory_usage: number;
    gpu_info?: string;
  };
  last_heartbeat: string;
}

export const getNodes = async (): Promise<NodeInfo[]> => {
  const response = await client.get<NodeInfo[]>('/nodes');
  return response.data;
};

export const getNodeDetail = async (nodeId: string): Promise<NodeInfo> => {
  const response = await client.get<NodeInfo>(`/nodes/${nodeId}`);
  return response.data;
};

export const deleteNode = async (nodeId: string) => {
  await client.delete(`/nodes/${nodeId}`);
};
