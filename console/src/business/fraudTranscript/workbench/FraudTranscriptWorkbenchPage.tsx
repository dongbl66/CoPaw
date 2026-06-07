import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fraudTranscriptResultApi } from "@/api/modules/fraudTranscriptResult";
import { unifiedResultApi } from "@/api/modules/unifiedResult";
import type { FraudTranscriptResultRecord } from "@/api/types/fraudTranscript";
import ResultPanel from "@/pages/Chat/result-panel/ResultPanel";
import type { StructuredResultEvent } from "@/pages/Chat/result-panel/types";
import type { ResultWorkbenchPageProps } from "@/business/common/registry/types";

function isStructuredResultEvent(
  value: unknown,
): value is StructuredResultEvent {
  return (
    !!value &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    (value as Record<string, unknown>).eventType === "structured_result" &&
    typeof (value as Record<string, unknown>).version === "string" &&
    !!(value as Record<string, unknown>).result &&
    typeof (value as Record<string, unknown>).result === "object"
  );
}

function toStructuredResultEventFromFraudRecord(
  result: FraudTranscriptResultRecord,
): StructuredResultEvent {
  if (isStructuredResultEvent(result.structured_result)) {
    return result.structured_result;
  }

  return {
    eventType: "structured_result",
    version: "1.0",
    title: result.title,
    subtitle: result.scene || undefined,
    result: {
      type: "business",
      payload: {
        title: result.title,
        summary: result.summary || undefined,
        scene: "fraud_transcript_report",
        basicInfo: result.basic_info,
        productInfo: result.product_info,
        opportunities: result.qa_records,
        attachments: [],
      },
    },
    meta: {
      bizModule: "fraud_transcript",
      source: "stored_result_fallback",
      timestamp: Date.parse(result.updated_at) || Date.now(),
    },
  };
}

function isFraudTranscriptDirectResult(
  result: StructuredResultEvent | null,
): boolean {
  if (!result) return false;
  if (result.meta?.bizModule === "fraud_transcript") return true;
  const payload = result.result.payload;
  return (
    !!payload &&
    typeof payload === "object" &&
    !Array.isArray(payload) &&
    (payload as { scene?: unknown }).scene === "fraud_transcript_report"
  );
}

export default function FraudTranscriptWorkbenchPage({
  sessionId,
  open,
  refreshSignal,
  directResult,
  onOpenChange,
}: ResultWorkbenchPageProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [activeRecord, setActiveRecord] =
    useState<FraudTranscriptResultRecord | null>(null);
  const [activeResult, setActiveResult] =
    useState<StructuredResultEvent | null>(null);

  const applyResultRecord = useCallback(
    (record: FraudTranscriptResultRecord) => {
      setActiveRecord(record);
      setActiveResult(toStructuredResultEventFromFraudRecord(record));
    },
    [],
  );

  const loadLatestResult = useCallback(async (): Promise<FraudTranscriptResultRecord | null> => {
    if (!sessionId || !open) {
      return null;
    }

    setLoading(true);
    try {
      const response = await unifiedResultApi.getLatestResult(
        sessionId,
        "fraud_transcript",
      );
      if (response.item) {
        const record = response.item as FraudTranscriptResultRecord;
        applyResultRecord(record);
        return record;
      }
      return null;
    } catch (error) {
      console.error("Failed to load fraud transcript result:", error);
      return null;
    } finally {
      setLoading(false);
    }
  }, [applyResultRecord, open, sessionId]);

  const saveCurrentResult = useCallback(async () => {
    const record = activeRecord ?? (await loadLatestResult());
    if (!record?.id || record.save_status === "saved") {
      return;
    }

    setSaveLoading(true);
    try {
      const savedResult = await fraudTranscriptResultApi.saveResult(
        record.id,
      );
      applyResultRecord(savedResult);
      window.dispatchEvent(new CustomEvent("fraud-transcript:results-updated"));
    } catch (error) {
      console.error("Failed to save fraud transcript result:", error);
    } finally {
      setSaveLoading(false);
    }
  }, [activeRecord, applyResultRecord, loadLatestResult]);

  useEffect(() => {
    if (isFraudTranscriptDirectResult(directResult)) {
      setActiveRecord(null);
      setActiveResult(directResult);
    }
  }, [directResult]);

  useEffect(() => {
    void loadLatestResult();
  }, [loadLatestResult, refreshSignal]);

  return (
    <ResultPanel
      open={open}
      result={activeResult}
      updatedAt={activeRecord?.updated_at ?? null}
      loading={loading}
      onRefresh={() => {
        void loadLatestResult();
      }}
      onSave={() => {
        void saveCurrentResult();
      }}
      onViewDetail={() => {
        if (activeRecord?.id) {
          navigate(`/biz/fraud-transcript/results/${activeRecord.id}`);
        }
      }}
      showViewDetail={!!activeRecord?.id}
      saveLoading={saveLoading}
      isSaved={activeRecord?.save_status === "saved"}
      onClose={() => onOpenChange(false)}
    />
  );
}
