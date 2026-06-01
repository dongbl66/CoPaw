import { getBusinessModules } from "./registry";
import type { BusinessMenuDeclaration } from "./types";

/**
 * 汇总所有业务模块菜单。
 */
export function composeBusinessMenus(): BusinessMenuDeclaration[] {
  return getBusinessModules()
    .flatMap((module) => module.menus)
    .sort((left, right) => (left.priority ?? 0) - (right.priority ?? 0));
}
