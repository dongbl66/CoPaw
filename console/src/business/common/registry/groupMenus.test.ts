import { describe, expect, it } from "vitest";
import type { BusinessMenuDeclaration } from "./types";
import {
  BUSINESS_MENU_GROUP_META,
  groupBusinessMenus,
} from "./groupMenus";

const menus: BusinessMenuDeclaration[] = [
  {
    key: "biz-marketing-opportunities",
    path: "/biz/marketing/opportunities",
    label: "市场商机",
    groupKey: "taishan-analysis-group",
    priority: 20,
    icon: "O",
  },
  {
    key: "biz-fae-government-opportunities",
    path: "/biz/fae/government-opportunities",
    label: "政企商机",
    groupKey: "fae-workspace-group",
    priority: 10,
    icon: "F",
  },
  {
    key: "biz-marketing-product-solutions",
    path: "/biz/marketing/product-solutions",
    label: "产品方案",
    groupKey: "taishan-analysis-group",
    priority: 10,
    icon: "P",
  },
];

describe("groupBusinessMenus", () => {
  it("groups business menus by group key and keeps menu priority order", () => {
    const groups = groupBusinessMenus(menus, BUSINESS_MENU_GROUP_META);

    expect(groups).toEqual([
      {
        key: "taishan-analysis-group",
        label: "泰山石膏",
        priority: 10,
        menus: [
          expect.objectContaining({ key: "biz-marketing-product-solutions" }),
          expect.objectContaining({ key: "biz-marketing-opportunities" }),
        ],
      },
      {
        key: "fae-workspace-group",
        label: "内部提效",
        priority: 20,
        menus: [expect.objectContaining({ key: "biz-fae-government-opportunities" })],
      },
    ]);
  });

  it("falls back to raw group key when metadata is missing", () => {
    const groups = groupBusinessMenus(
      [
        {
          key: "biz-unknown",
          path: "/biz/unknown",
          label: "未知菜单",
          groupKey: "unknown-group",
        },
      ],
      BUSINESS_MENU_GROUP_META,
    );

    expect(groups).toEqual([
      {
        key: "unknown-group",
        label: "unknown-group",
        priority: 0,
        menus: [expect.objectContaining({ key: "biz-unknown" })],
      },
    ]);
  });
});
