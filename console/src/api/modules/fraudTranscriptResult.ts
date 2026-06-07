import { request } from "../request";
import type {
  FraudTranscriptLatestResultResponse,
  FraudTranscriptResultListResponse,
  FraudTranscriptResultRecord,
} from "../types/fraudTranscript";

function resultPath(resultId: number): string {
  return `/backend/fraud-transcript/results/${encodeURIComponent(String(resultId))}`;
}

export const fraudTranscriptResultApi = {
  listResults: (savedOnly = false) =>
    request<FraudTranscriptResultListResponse>(
      `/backend/fraud-transcript/results${savedOnly ? "?saved_only=true" : ""}`,
    ),

  getLatestResult: (sessionId: string) =>
    request<FraudTranscriptLatestResultResponse>(
      `/backend/fraud-transcript/results/latest?session_id=${encodeURIComponent(
        sessionId,
      )}`,
    ),

  getResult: (resultId: number) =>
    request<FraudTranscriptResultRecord>(resultPath(resultId)),

  saveResult: (resultId: number) =>
    request<FraudTranscriptResultRecord>(`${resultPath(resultId)}/save`, {
      method: "POST",
    }),
};

