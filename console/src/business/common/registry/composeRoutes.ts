import { getBusinessModules } from "./registry";
import type { BusinessRouteDeclaration } from "./types";

/**
 * 汇总所有业务模块路由。
 */
export function composeBusinessRoutes(): BusinessRouteDeclaration[] {
  return getBusinessModules()
    .flatMap((module) => module.routes)
    .sort((left, right) => (left.priority ?? 0) - (right.priority ?? 0));
}
