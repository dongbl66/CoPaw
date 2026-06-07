import { chatApi } from "../../../api/modules/chat";
import type { MarketingResultRecord } from "../../../api/modules/marketingResult";
import type { FAEResultRecord } from "../../../api/modules/faeResult";
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
  console.debug(
    "[ResultPanel] toStructuredResultEventFromRecord called",
    result.id,
    result.title,
  );

  const structuredResult = result.info?.structuredResult;
  if (isStructuredResultEvent(structuredResult)) {
    console.debug(
      "[ResultPanel] Found valid structuredResult: type=%s",
      structuredResult.result?.type,
    );
    return structuredResult;
  }

  if (!result.summary) {
    console.debug(
      "[ResultPanel] No structuredResult found, and no summary to fallback",
    );
    return null;
  }

  console.debug("[ResultPanel] Falling back to summary text");
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
  console.debug("[ResultPanel] extractStructuredResultFromPayload called");

  if (!isRecord(payload)) {
    console.debug("[ResultPanel] Payload is not a record, returning null");
    return null;
  }

  const directStructuredResult = extractStructuredResultFromDirectEvent(payload);
  if (directStructuredResult) {
    console.debug(
      "[ResultPanel] Found direct structured_result_event: type=%s",
      directStructuredResult.result?.type,
    );
    return directStructuredResult;
  }

  const output = payload.output;
  if (!Array.isArray(output)) {
    console.debug("[ResultPanel] payload.output is not an array");
    return null;
  }

  console.debug("[ResultPanel] Searching in output array (length=%d)", output.length);
  for (const item of output) {
    if (!isRecord(item)) continue;
    const metadata = item.metadata;
    if (!isRecord(metadata)) continue;
    const structuredResult = metadata.structured_result;
    if (isStructuredResultEvent(structuredResult)) {
      console.debug(
        "[ResultPanel] Found structured_result in metadata: type=%s",
        structuredResult.result?.type,
      );
      return structuredResult;
    }
  }

  console.debug("[ResultPanel] No structured_result found in payload");
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

/**
 * 将后端存储的 FAE 结果记录转换为前端统一结构化结果事件。
 */
export function toStructuredResultEventFromFAERecord(
  result: FAEResultRecord,
): StructuredResultEvent | null {
  console.debug(
    "[ResultPanel] toStructuredResultEventFromFAERecord called",
    result.id,
    result.title,
  );

  // FAE results store the full StructuredResultEvent in info.structuredResult
  const structuredResult = result.info?.structuredResult;
  if (isStructuredResultEvent(structuredResult)) {
    console.debug(
      "[ResultPanel] Found valid FAE structuredResult: type=%s",
      structuredResult.result?.type,
    );
    return structuredResult;
  }

  // Fallback: build a text result from summary
  if (result.summary) {
    console.debug("[ResultPanel] Falling back to FAE summary text");
    return {
      eventType: "structured_result",
      version: "1.0",
      title: result.title,
      subtitle: result.scene || undefined,
      result: {
        type: "text",
        payload: { text: result.summary },
      },
      meta: {
        bizModule: "fae",
        source: "stored_result_fallback",
        timestamp: Date.parse(result.updated_at) || Date.now(),
      },
    };
  }

  return null;
}
