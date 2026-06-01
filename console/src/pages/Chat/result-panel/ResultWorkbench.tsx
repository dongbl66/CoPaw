import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { marketingResultApi } from "../../../api/modules/marketingResult";
import type { MarketingResultRecord } from "../../../api/modules/marketingResult";
import {
  getProductSolutionDetailPath,
} from "@/business/marketing/components/adapters";
import ResultPanel from "./ResultPanel";
import type { StructuredResultEvent } from "./types";
import { toStructuredResultEventFromRecord } from "./utils";

const RESULT_POLL_INTERVAL_MS = 5000;

export interface ResultWorkbenchProps {
  sessionId: string | null;
}

/**
 * 独立结果工作台，通过轮询后端结果接口驱动渲染，不依赖 chat SSE 解析。
 */
export default function ResultWorkbench({
  sessionId,
}: ResultWorkbenchProps) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [activeRecord, setActiveRecord] = useState<MarketingResultRecord | null>(
    null,
  );
  const [activeResult, setActiveResult] = useState<StructuredResultEvent | null>(
    null,
  );
  const latestResultIdRef = useRef<number | null>(null);

  const resetWorkbench = useCallback(() => {
    latestResultIdRef.current = null;
    setActiveRecord(null);
    setActiveResult(null);
    setOpen(true);
  }, []);

  const applyResultRecord = useCallback(
    (resultRecord: MarketingResultRecord) => {
      const nextResult = toStructuredResultEventFromRecord(resultRecord);
      if (!nextResult) {
        return;
      }

      setActiveRecord(resultRecord);
      setActiveResult(nextResult);
      if (latestResultIdRef.current !== resultRecord.id) {
        latestResultIdRef.current = resultRecord.id;
        if (nextResult.layout?.autoOpen !== false) {
          setOpen(true);
        }
      }
    },
    [],
  );

  const loadLatestResult = useCallback(async () => {
    if (!sessionId || document.hidden) {
      return;
    }

    setLoading(true);
    try {
      const response = await marketingResultApi.getLatestResult(sessionId);
      const latestItem = response.item;
      if (!latestItem) {
        return;
      }
      applyResultRecord(latestItem);
    } catch (error) {
      console.error("Failed to load latest marketing result:", error);
    } finally {
      setLoading(false);
    }
  }, [applyResultRecord, sessionId]);

  const openResultDetailPage = useCallback(() => {
    if (!activeRecord?.id || !activeResult) {
      return;
    }

    if (activeResult.result.type === "business") {
      navigate("/biz/marketing/opportunities");
      return;
    }

    navigate(getProductSolutionDetailPath(activeRecord.id));
  }, [activeRecord?.id, activeResult, navigate]);

  const saveCurrentResult = useCallback(async () => {
    if (!activeRecord?.id || activeRecord.save_status === "saved") {
      return;
    }

    setSaveLoading(true);
    try {
      const savedResult = await marketingResultApi.saveResult(activeRecord.id);
      applyResultRecord(savedResult);
    } catch (error) {
      console.error("Failed to save marketing result:", error);
    } finally {
      setSaveLoading(false);
    }
  }, [activeRecord?.id, activeRecord?.save_status, applyResultRecord]);

  useEffect(() => {
    if (!sessionId) {
      resetWorkbench();
      return;
    }

    resetWorkbench();
    void loadLatestResult();

    const timer = window.setInterval(() => {
      void loadLatestResult();
    }, RESULT_POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [loadLatestResult, resetWorkbench, sessionId]);

  const panelResult = useMemo(() => activeResult, [activeResult]);

  return (
    <ResultPanel
      open={open}
      result={panelResult}
      updatedAt={activeRecord?.updated_at || null}
      loading={loading}
      onRefresh={() => {
        void loadLatestResult();
      }}
      onSave={() => {
        void saveCurrentResult();
      }}
      onViewDetail={openResultDetailPage}
      showViewDetail={!!activeRecord?.id}
      saveLoading={saveLoading}
      isSaved={activeRecord?.save_status === "saved"}
      onClose={() => setOpen(false)}
    />
  );
}
