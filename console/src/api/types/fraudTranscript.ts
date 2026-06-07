export interface FraudTranscriptResultRecord {
  id: number;
  title: string;
  result_type: string;
  save_status: string;
  scene?: string | null;
  summary?: string | null;
  basic_info: Record<string, unknown>;
  product_info: Record<string, unknown>;
  qa_records: Array<Record<string, unknown>>;
  structured_result: Record<string, unknown>;
  session_id?: string | null;
  agent_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FraudTranscriptResultListResponse {
  items: FraudTranscriptResultRecord[];
}

export interface FraudTranscriptLatestResultResponse {
  item: FraudTranscriptResultRecord | null;
}

