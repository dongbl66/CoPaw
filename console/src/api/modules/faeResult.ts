import { request } from "../request";

// ── API response types (snake_case, matching backend) ──

export interface FAEOpportunityRecord {
  id: number;
  project_name: string;
  customer_name: string;
  city: string;
  industry: string;
  support_type: string;
  create_time: string;
  update_time: string;
  requirement_desc: string;
  opportunity_rating: string;
  opportunity_score: number | null;
  budget_min_yuan: number | null;
  budget_max_yuan: number | null;
  budget_note: string | null;
  display_content: Array<Record<string, unknown>>;
  session_id: string | null;
  agent_id: string | null;
}

export interface FAEOpportunityListResponse {
  items: FAEOpportunityRecord[];
}

export interface FAEOpportunityDetailResponse extends FAEOpportunityRecord {}

// ── Result types (for result panel) ──

export interface FAEResultRecord {
  id: number;
  title: string;
  result_type: string;
  save_status?: string;
  scene?: string | null;
  summary?: string | null;
  info: Record<string, unknown>;
  basic_info: Record<string, unknown>;
  detail_content?: Array<Record<string, unknown>>;
  display_content?: Array<Record<string, unknown>>;
  attachments?: Array<Record<string, unknown>>;
  session_id?: string | null;
  agent_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FAEResultLatestResponse {
  item: FAEResultRecord | null;
}

export interface FAEResultListResponse {
  items: FAEResultRecord[];
}

export interface FAEResultFromToolOutputRequest {
  tool_name?: string;
  tool_output: Record<string, unknown>;
  session_id?: string | null;
  agent_id?: string | null;
}

/**
 * FAE 政企商机 & 结果面板接口。
 */
export const faeResultApi = {
  // ── Government Opportunities ──
  listOpportunities: () =>
    request<FAEOpportunityListResponse>("/backend/fae/opportunities"),

  getOpportunity: (opportunityId: number | string) =>
    request<FAEOpportunityDetailResponse>(
      `/backend/fae/opportunities/${encodeURIComponent(opportunityId)}`,
    ),

  createOpportunity: (body: Record<string, unknown>) =>
    request<FAEOpportunityRecord>("/backend/fae/opportunities", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  updateOpportunity: (
    opportunityId: number | string,
    body: Record<string, unknown>,
  ) =>
    request<FAEOpportunityRecord>(
      `/backend/fae/opportunities/${encodeURIComponent(opportunityId)}`,
      {
        method: "PUT",
        body: JSON.stringify(body),
      },
    ),

  deleteOpportunity: (opportunityId: number | string) =>
    request<void>(
      `/backend/fae/opportunities/${encodeURIComponent(opportunityId)}`,
      { method: "DELETE" },
    ),

  // ── FAE Results (for result panel) ──
  listResults: (savedOnly = false) =>
    request<FAEResultListResponse>(
      `/backend/fae/results?saved_only=${savedOnly}`,
    ),

  getLatestResult: (sessionId: string) =>
    request<FAEResultLatestResponse>(
      `/backend/fae/results/latest?session_id=${encodeURIComponent(sessionId)}`,
    ),

  getResultDetail: (resultId: number | string) =>
    request<FAEResultRecord>(
      `/backend/fae/results/${encodeURIComponent(resultId)}`,
    ),

  saveResult: (resultId: number | string) =>
    request<FAEResultRecord>(
      `/backend/fae/results/${encodeURIComponent(resultId)}/save`,
      { method: "POST" },
    ),

  // ── Fallback: create result from tool output ──
  createResultFromToolOutput: (body: FAEResultFromToolOutputRequest) =>
    request<FAEResultRecord>("/backend/fae/results/from-tool-output", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
