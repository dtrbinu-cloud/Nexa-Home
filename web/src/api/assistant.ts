import { apiClient } from './client';

export interface PendingConfirmation {
  id: string;
  action_summary: string;
  affected_devices: string[];
  expires_at: string;
}

export interface AssistantChatResponse {
  reply: string;
  tool_called?: string;
  pending_confirmation?: boolean;
  confirmation_id?: string;
  confirmation_details?: string;
  audio_url?: string;
}

export interface AssistantHistoryItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export const assistantApi = {
  chat: (message: string) =>
    apiClient<AssistantChatResponse>('/api/assistant/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),

  confirmAction: (confirmationId: string, approved: boolean) =>
    apiClient<{ status: string; message: string; result?: any }>('/api/assistant/confirm', {
      method: 'POST',
      body: JSON.stringify({ confirmation_id: confirmationId, approved }),
    }),

  getHistory: () =>
    apiClient<AssistantHistoryItem[]>('/api/assistant/history'),

  clearHistory: () =>
    apiClient<{ status: string; message: string }>('/api/assistant/history', {
      method: 'DELETE',
    }),

  synthesizeTts: async (text: string): Promise<Blob> => {
    const res = await fetch('/api/assistant/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      credentials: 'include',
    });
    if (!res.ok) {
      throw new Error('TTS tidak tersedia');
    }
    return res.blob();
  },
};
