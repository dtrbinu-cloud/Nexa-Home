import { apiClient } from './client';

export interface AuditLogItem {
  id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  details: any;
  ip_address: string | null;
  created_at: string;
}

export const auditApi = {
  getLogs: async (limit: number = 30): Promise<AuditLogItem[]> => {
    try {
      const res = await apiClient<{ status: string; logs: AuditLogItem[] }>(
        `/api/audit-logs?limit=${limit}`
      );
      return res.logs || [];
    } catch {
      return [];
    }
  },
};
