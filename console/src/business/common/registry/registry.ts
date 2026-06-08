import type { BusinessModuleManifest } from "./types";
import { registerResultWorkbenchPage } from "./resultWorkbench";
import { registerStructuredResultAdapter } from "./structuredResultAdapters";

const manifests: BusinessModuleManifest[] = [];

/**
 * 注册前端业务模块。
 */
export function registerBusinessModule(
  manifest: BusinessModuleManifest,
): void {
  manifests.push(manifest);
  const resultWorkbench = manifest.resultWorkbench;
  if (Array.isArray(resultWorkbench)) {
    resultWorkbench.forEach(registerResultWorkbenchPage);
  } else if (resultWorkbench) {
    registerResultWorkbenchPage(resultWorkbench);
  }

  const structuredResultAdapters = manifest.structuredResultAdapters;
  if (Array.isArray(structuredResultAdapters)) {
    structuredResultAdapters.forEach(registerStructuredResultAdapter);
  } else if (structuredResultAdapters) {
    registerStructuredResultAdapter(structuredResultAdapters);
  }
}

/**
 * 获取所有已注册业务模块。
 */
export function getBusinessModules(): BusinessModuleManifest[] {
  return [...manifests];
}
