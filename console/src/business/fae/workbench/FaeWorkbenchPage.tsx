import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { faeResultApi } from "@/api/modules/faeResult";
import type { FAEResultRecord } from "@/api/modules/faeResult";
import { unifiedResultApi } from "@/api/modules/unifiedResult";
import ResultPanel from "@/pages/Chat/result-panel/ResultPanel";
import type { StructuredResultEvent } from "@/pages/Chat/result-panel/types";
import { toStructuredResultEventFromFAERecord } from "@/pages/Chat/result-panel/utils";
import type { ResultWorkbenchPageProps } from "@/business/common/registry/types";

function isFaeDirectResult(result: StructuredResultEvent | null): boolean {
  return (
    result?.meta?.bizModule === "fae" ||
    result?.result?.type === "government_opportunity"
  );
}

export default function FaeWorkbenchPage({
  sessionId,
  open,
  refreshSignal,
  directResult,
  onOpenChange,
}: ResultWorkbenchPageProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [activeRecord, setActiveRecord] = useState<FAEResultRecord | null>(
    null,
  );
  const [activeResult, setActiveResult] =
    useState<StructuredResultEvent | null>(null);

  const applyResultRecord = useCallback((record: FAEResultRecord) => {
    const structuredResult = toStructuredResultEventFromFAERecord(record);
    setActiveRecord(record);
    setActiveResult(structuredResult);
  }, []);

  const loadLatestResult = useCallback(async (): Promise<FAEResultRecord | null> => {
    if (!sessionId || !open) {
      return null;
    }

    setLoading(true);
    try {
      const response = await unifiedResultApi.getLatestResult(sessionId, "fae");
      if (response.item) {
        const record = response.item as FAEResultRecord;
        applyResultRecord(record);
        return record;
      }
      return null;
    } catch (error) {
      console.error("Failed to load FAE result:", error);
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
      const savedResult = await faeResultApi.saveResult(record.id);
      applyResultRecord(savedResult);
      window.dispatchEvent(new CustomEvent("fae:results-updated"));
    } catch (error) {
      console.error("Failed to save FAE result:", error);
    } finally {
      setSaveLoading(false);
    }
  }, [activeRecord, applyResultRecord, loadLatestResult]);

  useEffect(() => {
    if (isFaeDirectResult(directResult)) {
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
          navigate(`/biz/fae/results/${activeRecord.id}`);
        }
      }}
      showViewDetail={!!activeRecord?.id}
      saveLoading={saveLoading}
      isSaved={activeRecord?.save_status === "saved"}
      onClose={() => onOpenChange(false)}
    />
  );
}
