import client from './client';

export interface SystemStatus {
  initialized: boolean;
  workdir?: string;
}

export const getSystemStatus = async (): Promise<SystemStatus> => {
  // In real implementation, this hits GET /api/system/status
  // For now we can mock it or assume the backend endpoint exists
  try {
    const response = await client.get<SystemStatus>('/system/status');
    return response.data;
  } catch (error) {
    // If backend is not ready, we might assume not initialized
    console.error("Failed to check system status", error);
    throw error;
  }
};

export const setupWorkDir = async (path: string): Promise<void> => {
  await client.post('/system/setup', { workdir: path });
};
