import { request } from "../request";

export interface MarketingResultAttachment {
  id: number;
  result_id: number;
  file_name: string;
  file_type: string;
  mime_type?: string | null;
  file_url?: string | null;
  preview_url?: string | null;
  download_url?: string | null;
  file_path?: string | null;
  file_id?: string | null;
  file_size?: number | null;
  page_index?: number | null;
  sort_order: number;
  source_type?: string | null;
  extra: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MarketingResultRecord {
  id: number;
  title: string;
  result_type: string;
  save_status?: string;
  scene?: string | null;
  summary?: string | null;
  detail_content: Array<Record<string, unknown>>;
  info: Record<string, unknown>;
  basic_info: Record<string, unknown>;
  product_info: Record<string, unknown>;
  attachments: MarketingResultAttachment[];
  session_id?: string | null;
  agent_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MarketingLatestResultResponse {
  item: MarketingResultRecord | null;
}

export interface MarketingResultListResponse {
  items: MarketingResultRecord[];
}

export interface MarketingOpportunityRecord {
  id: number;
  title: string;
  opportunity_type?: string | null;
  region?: string | null;
  source?: string | null;
  publish_time?: string | null;
  deadline?: string | null;
  credibility?: number | null;
  contact?: string | null;
  budget?: number | null;
  purchase_amount?: number | null;
  link_status?: string | null;
  reason?: string | null;
  original_link?: string | null;
  level?: string | null;
  summary?: string | null;
  session_id?: string | null;
  agent_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MarketingOpportunityListResponse {
  items: MarketingOpportunityRecord[];
}

/**
 * 营销结果工作台接口。
 */
export const marketingResultApi = {
  listSavedResults: () =>
    request<MarketingResultListResponse>(
      "/backend/marketing/results?saved_only=true",
    ),

  getLatestResult: (sessionId: string) =>
    request<MarketingLatestResultResponse>(
      `/backend/marketing/results/latest?session_id=${encodeURIComponent(sessionId)}`,
    ),

  getResultDetail: (resultId: number) =>
    request<MarketingResultRecord>(
      `/backend/marketing/results/${encodeURIComponent(String(resultId))}`,
    ),

  getOpportunityDetail: (opportunityId: number) =>
    request<MarketingOpportunityRecord>(
      `/backend/marketing/opportunities/${encodeURIComponent(String(opportunityId))}`,
    ),

  saveResult: (resultId: number) =>
    request<MarketingResultRecord>(
      `/backend/marketing/results/${encodeURIComponent(String(resultId))}/save`,
      {
        method: "POST",
      },
    ),

  listOpportunities: () =>
    request<MarketingOpportunityListResponse>(
      "/backend/marketing/opportunities",
    ),
};
