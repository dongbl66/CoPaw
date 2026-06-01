import { request } from "../request";

export interface WeeklyReport {
  id: string;
  title: string;
  period_start: string;
  period_end: string;
  author: string;
  content: string;
  project_name?: string;
  status: "draft" | "submitted" | "archived";
  created_at: number;
  updated_at: number;
  tags: string[];
}

export interface CreateWeeklyReportRequest {
  title: string;
  period_start: string;
  period_end: string;
  author: string;
  content: string;
  project_name?: string;
  tags?: string[];
}

export interface UpdateWeeklyReportRequest {
  title?: string;
  content?: string;
  status?: string;
  project_name?: string;
  tags?: string[];
}

export interface PushMessage {
  id: string;
  text: string;
}

export interface InboxEvent {
  id: string;
  agent_id: string;
  source_type: string;
  source_id: string;
  event_type: string;
  status: string;
  severity: string;
  title: string;
  body: string;
  payload?: Record<string, unknown>;
  read: boolean;
  created_at: number;
}

export interface InboxTrace {
  run_id: string;
  created_at: number;
  completed_at: number | null;
  status: string;
  meta: Record<string, unknown>;
  events: Array<{
    at: number;
    event: Record<string, unknown>;
  }>;
  error?: string;
}

export interface PendingApproval {
  request_id: string;
  session_id: string;
  root_session_id: string;
  owner_agent_id?: string;
  agent_id: string;
  tool_name: string;
  severity: string;
  findings_count: number;
  findings_summary: string;
  tool_params: Record<string, unknown>;
  created_at: number;
  timeout_seconds: number;
}

export const consoleApi = {
  getPushMessages: (sessionId?: string) =>
    request<{ messages: PushMessage[]; pending_approvals: PendingApproval[] }>(
      sessionId
        ? `/console/push-messages?session_id=${sessionId}`
        : "/console/push-messages",
    ),

  getInboxEvents: (params?: {
    limit?: number;
    offset?: number;
    source_type?: string;
    status?: string;
    agent_id?: string;
    unread_only?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.limit !== undefined) query.set("limit", String(params.limit));
    if (params?.offset !== undefined)
      query.set("offset", String(params.offset));
    if (params?.source_type) query.set("source_type", params.source_type);
    if (params?.status) query.set("status", params.status);
    if (params?.agent_id) query.set("agent_id", params.agent_id);
    if (params?.unread_only !== undefined) {
      query.set("unread_only", String(params.unread_only));
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<{ events: InboxEvent[] }>(`/console/inbox/events${suffix}`);
  },

  markInboxRead: (payload: { event_ids?: string[]; all?: boolean }) =>
    request<{ updated: number }>("/console/inbox/read", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteInboxEvent: (eventId: string) =>
    request<{
      deleted: boolean;
      trace_deleted?: boolean;
      run_id?: string | null;
    }>(`/console/inbox/events/${encodeURIComponent(eventId)}`, {
      method: "DELETE",
    }),

  getInboxTrace: (runId: string) =>
    request<InboxTrace>(`/console/inbox/traces/${encodeURIComponent(runId)}`),

  // Weekly Report APIs
  createWeeklyReport: (req: CreateWeeklyReportRequest) =>
    request<WeeklyReport>("/console/weekly-reports", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  listWeeklyReports: (params?: {
    status?: string;
    project_name?: string;
    author?: string;
    limit?: number;
    offset?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.project_name) query.set("project_name", params.project_name);
    if (params?.author) query.set("author", params.author);
    if (params?.limit !== undefined) query.set("limit", String(params.limit));
    if (params?.offset !== undefined)
      query.set("offset", String(params.offset));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<{ reports: WeeklyReport[]; total: number }>(
      `/console/weekly-reports${suffix}`,
    );
  },

  getWeeklyReport: (reportId: string) =>
    request<WeeklyReport>(`/console/weekly-reports/${encodeURIComponent(reportId)}`),

  updateWeeklyReport: (reportId: string, req: UpdateWeeklyReportRequest) =>
    request<WeeklyReport>(`/console/weekly-reports/${encodeURIComponent(reportId)}`, {
      method: "PUT",
      body: JSON.stringify(req),
    }),

  deleteWeeklyReport: (reportId: string) =>
    request<{ deleted: boolean }>(`/console/weekly-reports/${encodeURIComponent(reportId)}`, {
      method: "DELETE",
    }),
};
