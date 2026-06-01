import type { BusinessModuleManifest } from "./types";

const manifests: BusinessModuleManifest[] = [];

/**
 * 注册前端业务模块。
 */
export function registerBusinessModule(
  manifest: BusinessModuleManifest,
): void {
  manifests.push(manifest);
}

/**
 * 获取所有已注册业务模块。
 */
export function getBusinessModules(): BusinessModuleManifest[] {
  return [...manifests];
}
