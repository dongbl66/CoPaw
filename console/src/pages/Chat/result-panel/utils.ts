import { chatApi } from "../../../api/modules/chat";
import type { MarketingResultRecord } from "../../../api/modules/marketingResult";
import type {
  StructuredResultEvent,
  StructuredResultPushEvent,
} from "./types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function isStructuredResultEvent(
  value: unknown,
): value is StructuredResultEvent {
  return (
    isRecord(value) &&
    value.eventType === "structured_result" &&
    typeof value.version === "string" &&
    isRecord(value.result)
  );
}

function isStructuredResultPushEvent(
  value: unknown,
): value is StructuredResultPushEvent {
  return (
    isRecord(value) &&
    value.object === "structured_result_event" &&
    typeof value.status === "string" &&
    isStructuredResultEvent(value.structured_result)
  );
}

/**
 * 将后端存储的营销结果记录转换为前端统一结构化结果事件。
 */
export function toStructuredResultEventFromRecord(
  result: MarketingResultRecord,
): StructuredResultEvent | null {
  const structuredResult = result.info?.structuredResult;
  if (isStructuredResultEvent(structuredResult)) {
    console.log(
      "[result-panel:utils] toStructuredResultEvent: found structuredResult in info, type=%s title=%s",
      (structuredResult as StructuredResultEvent).result.type,
      (structuredResult as StructuredResultEvent).title,
    );
    return structuredResult;
  }

  console.log(
    "[result-panel:utils] toStructuredResultEvent: no structuredResult in info, "
    + "info_keys=%s summary=%s fallback_to_text=%s",
    result.info ? Object.keys(result.info).join(",") : "null",
    result.summary ? "present" : "missing",
    !!result.summary,
  );

  if (!result.summary) {
    return null;
  }

  return {
    eventType: "structured_result",
    version: "1.0",
    title: result.title,
    subtitle: result.scene || undefined,
    result: {
      type: "text",
      payload: {
        text: result.summary,
      },
    },
    meta: {
      bizModule: "marketing",
      source: "stored_result_fallback",
      timestamp: Date.parse(result.updated_at) || Date.now(),
    },
  };
}

/**
 * 从聊天响应 payload 中提取结构化结果事件。
 */
export function extractStructuredResultFromPayload(
  payload: unknown,
): StructuredResultEvent | null {
  if (!isRecord(payload)) return null;

  const directStructuredResult = extractStructuredResultFromDirectEvent(payload);
  if (directStructuredResult) {
    return directStructuredResult;
  }

  const output = payload.output;
  if (!Array.isArray(output)) return null;

  for (const item of output) {
    if (!isRecord(item)) continue;
    const metadata = item.metadata;
    if (!isRecord(metadata)) continue;
    const structuredResult = metadata.structured_result;
    if (isStructuredResultEvent(structuredResult)) {
      return structuredResult;
    }
  }

  return null;
}

function extractStructuredResultFromDirectEvent(
  payload: Record<string, unknown>,
): StructuredResultEvent | null {
  if (payload.object !== "structured_result_event") {
    return null;
  }

  const structuredResult = payload.structured_result;
  if (!isRecord(structuredResult)) {
    return null;
  }

  if (
    structuredResult.eventType === "structured_result" &&
    isRecord(structuredResult.result)
  ) {
    return isStructuredResultPushEvent(payload)
      ? payload.structured_result
      : null;
  }

  return null;
}

/**
 * 将 PDF 结果中的 filePath/fileUrl 规范化为可展示的 URL。
 */
export function resolvePdfDisplayUrl(payload: {
  fileUrl?: string;
  filePath?: string;
}): string {
  if (payload.fileUrl) {
    return chatApi.filePreviewUrl(payload.fileUrl);
  }
  if (payload.filePath) {
    return chatApi.filePreviewUrl(payload.filePath);
  }
  return "";
}
