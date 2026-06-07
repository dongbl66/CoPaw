import type {
  BusinessResultWorkbenchManifest,
  ResultWorkbenchPageProps,
} from "./types";
import type React from "react";
import type { ResultBizModule } from "@/api/modules/unifiedResult";

const resultWorkbenchPages = new Map<
  ResultBizModule,
  React.ComponentType<ResultWorkbenchPageProps>
>();

export function registerResultWorkbenchPage(
  manifest: BusinessResultWorkbenchManifest,
): void {
  resultWorkbenchPages.set(manifest.bizModule, manifest.Page);
}

export function getResultWorkbenchPage(
  bizModule: ResultBizModule | null | undefined,
): React.ComponentType<ResultWorkbenchPageProps> | null {
  if (!bizModule) return null;
  return resultWorkbenchPages.get(bizModule) ?? null;
}

export function resetResultWorkbenchPagesForTest(): void {
  if (import.meta.env.MODE !== "test") {
    return;
  }
  resultWorkbenchPages.clear();
}
