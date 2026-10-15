import { apiClient } from './client';

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  database: {
    status: string;
    journal_mode: string;
  };
  mqtt?: {
    connected: boolean;
  };
  timestamp?: string;
}

export const healthApi = {
  check: () => apiClient<HealthResponse>('/api/health'),
};
