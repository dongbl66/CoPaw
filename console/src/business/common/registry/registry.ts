import type { BusinessModuleManifest } from "./types";
import { registerResultWorkbenchPage } from "./resultWorkbench";

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
}

/**
 * 获取所有已注册业务模块。
 */
export function getBusinessModules(): BusinessModuleManifest[] {
  return [...manifests];
}
