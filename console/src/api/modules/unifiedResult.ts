import { request } from "../request";
import type { MarketingResultRecord } from "./marketingResult";
import type { FAEResultRecord } from "./faeResult";
import type { FraudTranscriptResultRecord } from "../types/fraudTranscript";

export type ResultBizModule = "marketing" | "fae" | "fraud_transcript";

export type UnifiedResultRecord =
  | MarketingResultRecord
  | FAEResultRecord
  | FraudTranscriptResultRecord;

export interface UnifiedLatestResultResponse {
  item: UnifiedResultRecord | null;
  biz_module?: ResultBizModule | null;
}

export const unifiedResultApi = {
  getLatestResult: (sessionId: string, bizModule?: ResultBizModule | null) => {
    const params = new URLSearchParams({ session_id: sessionId });
    if (bizModule) {
      params.set("biz_module", bizModule);
    }
    return request<UnifiedLatestResultResponse>(
      `/backend/results/latest?${params.toString()}`,
    );
  },
};
