import { apiFetch } from './client';

export interface HealthData {
  status: string;
  app: string;
  version: string;
  timestamp: string;
}

export interface ReadyData {
  status: string;
  database: {
    status: string;
    mode: string;
    connected: boolean;
  };
  vector_store: {
    type: string;
    ready: boolean;
  };
  embedding_provider: string;
  llm_configured: boolean;
  timestamp: string;
}

export const healthApi = {
  getHealth: () => apiFetch<HealthData>('health', { method: 'GET' }),
  getReady: () => apiFetch<ReadyData>('ready', { method: 'GET' }),
};
