import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { marketingResultApi } from "../../../api/modules/marketingResult";
import type { MarketingResultRecord } from "../../../api/modules/marketingResult";
import { faeResultApi } from "../../../api/modules/faeResult";
import type { FAEResultRecord } from "../../../api/modules/faeResult";
import { fraudTranscriptResultApi } from "../../../api/modules/fraudTranscriptResult";
import type { FraudTranscriptResultRecord } from "../../../api/types/fraudTranscript";
import { unifiedResultApi } from "../../../api/modules/unifiedResult";
import type { ResultBizModule } from "../../../api/modules/unifiedResult";
import { getResultWorkbenchPage } from "@/business/common/registry/resultWorkbench";
import { getProductSolutionDetailPath } from "@/business/marketing/components/adapters";
import ResultPanel from "./ResultPanel";
import type { StructuredResultEvent } from "./types";
import {
  toStructuredResultEventFromRecord,
  toStructuredResultEventFromFAERecord,
} from "./utils";

const RESULT_POLL_INTERVAL_MS = 5000;

type ActiveRecord =
  | MarketingResultRecord
  | FAEResultRecord
  | FraudTranscriptResultRecord;

function isMarketingRecord(r: ActiveRecord): r is MarketingResultRecord {
  return "detail_content" in r;
}

function isFraudTranscriptRecord(
  r: ActiveRecord,
): r is FraudTranscriptResultRecord {
  return "structured_result" in r && "qa_records" in r;
}

function recordUpdatedAt(r: ActiveRecord): string {
  return r.updated_at;
}

function getSaveStatus(r: ActiveRecord): string | undefined {
  return r.save_status;
}

function bizModuleFromStructuredResult(
  result: StructuredResultEvent | null,
): ResultBizModule | null {
  const metaModule = result?.meta?.bizModule;
  if (
    metaModule === "marketing" ||
    metaModule === "fae" ||
    metaModule === "fraud_transcript"
  ) {
    return metaModule;
  }

  const payload = result?.result?.payload;
  if (payload && typeof payload === "object" && !Array.isArray(payload)) {
    const scene = (payload as { scene?: unknown }).scene;
    if (scene === "fraud_transcript_report") {
      return "fraud_transcript";
    }
  }

  if (result?.result?.type === "government_opportunity") {
    return "fae";
  }

  return null;
}

function bizModuleFromRecord(record: ActiveRecord): ResultBizModule {
  if (isFraudTranscriptRecord(record)) return "fraud_transcript";
  if (isMarketingRecord(record)) return "marketing";
  return "fae";
}

function toStructuredResultEventFromFraudRecord(
  result: FraudTranscriptResultRecord,
): StructuredResultEvent | null {
  const structuredResult = result.structured_result;
  if (
    structuredResult?.eventType === "structured_result" &&
    typeof structuredResult.version === "string" &&
    structuredResult.result &&
    typeof structuredResult.result === "object"
  ) {
    return structuredResult as unknown as StructuredResultEvent;
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

export interface ResultWorkbenchProps {
  sessionId: string | null;
  open?: boolean;
  defaultBizModule?: ResultBizModule | null;
  refreshSignal?: number;
  directResult?: StructuredResultEvent | null;
  pendingToolResult?: unknown;
  onOpenChange?: (open: boolean) => void;
}

/**
 * 独立结果工作台，通过轮询后端结果接口驱动渲染，不依赖 chat SSE 解析。
 * 优先查后端存储，无数据时使用 pendingToolResult 调用 fallback 补存。
 */
function LegacyResultWorkbenchPage({
  sessionId,
  open = true,
  defaultBizModule = null,
  refreshSignal = 0,
  directResult = null,
  pendingToolResult = null,
  onOpenChange = () => undefined,
}: ResultWorkbenchProps) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [activeRecord, setActiveRecord] = useState<ActiveRecord | null>(null);
  const [activeResult, setActiveResult] =
    useState<StructuredResultEvent | null>(null);
  const latestResultIdRef = useRef<number | null>(null);
  const lastSessionIdRef = useRef<string | null>(null);
  const preferredBizModuleRef = useRef<ResultBizModule | null>(null);
  const pendingRef = useRef<unknown>(null);
  pendingRef.current = pendingToolResult;

  const resetWorkbench = useCallback((resetBizModule = false) => {
    latestResultIdRef.current = null;
    setActiveRecord(null);
    setActiveResult(null);
    if (resetBizModule) {
      preferredBizModuleRef.current = null;
    }
  }, []);

  const applyResultRecord = useCallback((resultRecord: ActiveRecord) => {
    console.debug(
      "[ResultWorkbench] applyResultRecord: id=%s",
      resultRecord.id,
    );
    const nextResult = isFraudTranscriptRecord(resultRecord)
      ? toStructuredResultEventFromFraudRecord(resultRecord)
      : isMarketingRecord(resultRecord)
      ? toStructuredResultEventFromRecord(resultRecord)
      : toStructuredResultEventFromFAERecord(resultRecord);
    if (!nextResult) {
      console.debug(
        "[ResultWorkbench] applyResultRecord: no structured result",
      );
      return;
    }

    console.debug(
      "[ResultWorkbench] applyResultRecord: setting active result - type=%s, title=%s",
      nextResult.result?.type,
      nextResult.title,
    );
    setActiveRecord(resultRecord);
    setActiveResult(nextResult);
    preferredBizModuleRef.current = bizModuleFromRecord(resultRecord);
    latestResultIdRef.current = resultRecord.id;
  }, []);

  const loadLatestResultForModule = useCallback(
    async (bizModule: ResultBizModule): Promise<ActiveRecord | null> => {
      const response = await unifiedResultApi.getLatestResult(
        sessionId!,
        bizModule,
      );
      return response.item;
    },
    [sessionId],
  );

  const loadLatestResult = useCallback(async () => {
    if (!sessionId || !open || document.hidden) {
      return;
    }

    console.debug(
      "[ResultWorkbench] Loading latest results for session:",
      sessionId,
    );
    setLoading(true);
    try {
      const targetBizModule =
        bizModuleFromStructuredResult(directResult) ||
        preferredBizModuleRef.current ||
        defaultBizModule;

      if (targetBizModule) {
        const latestItem = await loadLatestResultForModule(targetBizModule);
        if (latestItem) {
          applyResultRecord(latestItem);
        }
        return;
      }

      console.debug(
        "[ResultWorkbench] Skip latest result load because biz module is unknown",
      );
    } catch (error) {
      console.error("[ResultWorkbench] Failed to load latest results:", error);
    } finally {
      setLoading(false);
    }
  }, [
    applyResultRecord,
    directResult,
    defaultBizModule,
    loadLatestResultForModule,
    sessionId,
    open,
  ]);

  const openResultDetailPage = useCallback(() => {
    if (!activeRecord?.id || !activeResult) {
      return;
    }

    // FAE result → navigate to government opportunities detail
    if (activeResult.result.type === "government_opportunity") {
      const info = (activeRecord as FAEResultRecord).info;
      if (info && typeof info.opportunityId === "number") {
        navigate(
          `/biz/fae/government-opportunities/${encodeURIComponent(
            info.opportunityId,
          )}`,
        );
        return;
      }
      navigate("/biz/fae/government-opportunities");
      return;
    }

    if (activeResult.result.type === "business") {
      const payload = activeResult.result.payload as { scene?: unknown };
      if (payload.scene === "fraud_transcript_report") {
        navigate(`/biz/fraud-transcript/results/${activeRecord.id}`);
        return;
      }
      navigate("/biz/marketing/opportunities");
      return;
    }

    navigate(getProductSolutionDetailPath(activeRecord.id));
  }, [activeRecord, activeResult, navigate]);

  const saveCurrentResult = useCallback(async () => {
    if (!activeRecord?.id || getSaveStatus(activeRecord) === "saved") {
      return;
    }

    setSaveLoading(true);
    try {
      if (isMarketingRecord(activeRecord)) {
        const savedResult = await marketingResultApi.saveResult(
          activeRecord.id,
        );
        applyResultRecord(savedResult);
      } else if (isFraudTranscriptRecord(activeRecord)) {
        const savedResult = await fraudTranscriptResultApi.saveResult(
          activeRecord.id,
        );
        applyResultRecord(savedResult);
      } else {
        const savedResult = await faeResultApi.saveResult(activeRecord.id);
        applyResultRecord(savedResult);
      }
    } catch (error) {
      console.error("Failed to save result:", error);
    } finally {
      setSaveLoading(false);
    }
  }, [activeRecord, applyResultRecord]);

  // Gate polling by open state and react to refreshSignal
  useEffect(() => {
    if (!sessionId || !open) {
      if (!sessionId) {
        lastSessionIdRef.current = null;
        resetWorkbench(true);
      }
      return;
    }

    if (lastSessionIdRef.current !== sessionId) {
      lastSessionIdRef.current = sessionId;
      resetWorkbench(true);
    }
    void loadLatestResult();

    const timer = window.setInterval(() => {
      void loadLatestResult();
    }, RESULT_POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
    };
    // refreshSignal is intentionally in deps to retrigger polling on "结果显示" click
  }, [loadLatestResult, resetWorkbench, sessionId, open, refreshSignal]);

  useEffect(() => {
    if (!directResult) return;
    setActiveRecord(null);
    setActiveResult(directResult);
    preferredBizModuleRef.current = bizModuleFromStructuredResult(directResult);
  }, [directResult]);

  const panelResult = useMemo(() => activeResult, [activeResult]);

  const isInlineDetail =
    activeResult?.result?.type === "government_opportunity";

  return (
    <ResultPanel
      open={open}
      result={panelResult}
      updatedAt={activeRecord ? recordUpdatedAt(activeRecord) : null}
      loading={loading}
      onRefresh={() => {
        void loadLatestResult();
      }}
      onSave={() => {
        void saveCurrentResult();
      }}
      onViewDetail={isInlineDetail ? undefined : openResultDetailPage}
      showViewDetail={isInlineDetail ? false : !!activeRecord?.id}
      saveLoading={saveLoading}
      isSaved={activeRecord ? getSaveStatus(activeRecord) === "saved" : false}
      onClose={() => onOpenChange(false)}
    />
  );
}

export default function ResultWorkbench(props: ResultWorkbenchProps) {
  const registeredBizModule =
    bizModuleFromStructuredResult(props.directResult ?? null) ||
    props.defaultBizModule ||
    null;
  const RegisteredWorkbenchPage = getResultWorkbenchPage(registeredBizModule);

  if (RegisteredWorkbenchPage) {
    return (
      <RegisteredWorkbenchPage
        sessionId={props.sessionId}
        open={props.open ?? true}
        refreshSignal={props.refreshSignal ?? 0}
        directResult={props.directResult ?? null}
        pendingToolResult={props.pendingToolResult}
        onOpenChange={props.onOpenChange ?? (() => undefined)}
      />
    );
  }

  return <LegacyResultWorkbenchPage {...props} />;
}
