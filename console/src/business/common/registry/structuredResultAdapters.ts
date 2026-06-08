import type {
  StructuredResultEvent,
  StructuredResultType,
} from "@/pages/Chat/result-panel/types";
import type { ResultBizModule } from "@/api/modules/unifiedResult";

export interface StructuredResultAdapterManifest {
  bizModule?: ResultBizModule;
  resultType: StructuredResultType;
  adapt: (result: StructuredResultEvent) => StructuredResultEvent | null;
}

const adapters: StructuredResultAdapterManifest[] = [];

export function registerStructuredResultAdapter(
  manifest: StructuredResultAdapterManifest,
): void {
  adapters.push(manifest);
}

export function adaptStructuredResult(
  result: StructuredResultEvent,
): StructuredResultEvent {
  for (const adapter of adapters) {
    if (adapter.resultType !== result.result.type) {
      continue;
    }
    if (
      adapter.bizModule &&
      result.meta?.bizModule &&
      adapter.bizModule !== result.meta.bizModule
    ) {
      continue;
    }

    const adapted = adapter.adapt(result);
    if (adapted) {
      return adapted;
    }
  }
  return result;
}

export function resetStructuredResultAdaptersForTest(): void {
  if (import.meta.env.MODE !== "test") {
    return;
  }
  adapters.length = 0;
}
