import type { BusinessMenuDeclaration } from "./types";

/**
 * 业务菜单分组元信息。
 */
export interface BusinessMenuGroupMeta {
  label: string;
  priority?: number;
}

/**
 * 侧边栏业务分组后的结构。
 */
export interface BusinessMenuGroup {
  key: string;
  label: string;
  priority: number;
  menus: BusinessMenuDeclaration[];
}

export const BUSINESS_MENU_GROUP_META: Record<string, BusinessMenuGroupMeta> = {
  "taishan-analysis-group": {
    label: "泰山石膏",
    priority: 10,
  },
  "fae-workspace-group": {
    label: "内部提效",
    priority: 20,
  },
};

/**
 * 将业务菜单按 groupKey 分组，并在组内按 priority 排序。
 */
export function groupBusinessMenus(
  menus: BusinessMenuDeclaration[],
  groupMeta: Record<string, BusinessMenuGroupMeta>,
): BusinessMenuGroup[] {
  const groups = new Map<string, BusinessMenuGroup>();

  menus.forEach((menu) => {
    const meta = groupMeta[menu.groupKey];
    const existingGroup = groups.get(menu.groupKey);
    const nextGroup =
      existingGroup ??
      {
        key: menu.groupKey,
        label: meta?.label ?? menu.groupKey,
        priority: meta?.priority ?? 0,
        menus: [],
      };

    nextGroup.menus.push(menu);
    groups.set(menu.groupKey, nextGroup);
  });

  return [...groups.values()]
    .map((group) => ({
      ...group,
      menus: [...group.menus].sort(
        (left, right) => (left.priority ?? 0) - (right.priority ?? 0),
      ),
    }))
    .sort((left, right) => left.priority - right.priority);
}
