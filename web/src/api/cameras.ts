import { apiClient } from './client';

export interface CameraItem {
  id: string;
  name: string;
  room_id: string;
  status: 'online' | 'offline';
  privacy_mode: boolean;
  privacy_schedule?: string | null;
  audio_enabled: boolean;
  ai_enabled: boolean;
  retention_days: number;
  motion_threshold: number;
  created_at: string;
}

export interface MotionEventItem {
  id: string;
  camera_id: string;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  file_size_bytes: number;
  has_thumbnail: boolean;
  created_at: string;
}

export interface PairingCodeResponse {
  code: string;
  camera_name: string;
  room_id: string;
  expires_at: string;
}

export const camerasApi = {
  getCameras: () => apiClient<CameraItem[]>('/api/cameras'),

  createPairingCode: (camera_name: string, room_id: string) =>
    apiClient<PairingCodeResponse>('/api/cameras/pairing-codes', {
      method: 'POST',
      body: JSON.stringify({ camera_name, room_id }),
    }),

  togglePrivacy: (id: string, privacy_mode: boolean) =>
    apiClient<{ status: string; camera_id: string; privacy_mode: boolean }>(
      `/api/cameras/${id}/privacy`,
      {
        method: 'PATCH',
        body: JSON.stringify({ privacy_mode }),
      }
    ),

  toggleAudio: (id: string, audio_enabled: boolean) =>
    apiClient<{ status: string; camera_id: string; audio_enabled: boolean }>(
      `/api/cameras/${id}/audio`,
      {
        method: 'PATCH',
        body: JSON.stringify({ audio_enabled }),
      }
    ),

  toggleAI: (id: string, ai_enabled: boolean) =>
    apiClient<{ status: string; camera_id: string; ai_enabled: boolean }>(
      `/api/cameras/${id}/ai`,
      {
        method: 'PATCH',
        body: JSON.stringify({ ai_enabled }),
      }
    ),

  revokeCamera: (id: string) =>
    apiClient<{ status: string; message: string }>(`/api/cameras/${id}/revoke`, {
      method: 'POST',
    }),

  getEvents: (id: string) => apiClient<MotionEventItem[]>(`/api/cameras/${id}/events`),

  getSnapshotUrl: (id: string) => `/api/cameras/${id}/snapshot`,

  getClipUrl: (camId: string, clipId: string) => `/api/cameras/${camId}/clips/${clipId}`,
};
