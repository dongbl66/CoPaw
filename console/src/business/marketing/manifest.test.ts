import { describe, expect, it } from "vitest";
import marketingManifest from "./manifest";

describe("marketingManifest", () => {
  it("only exposes list pages in sidebar menus", () => {
    expect(marketingManifest.menus).toEqual([
      expect.objectContaining({
        key: "biz-marketing-product-solutions",
        groupKey: "taishan-analysis-group",
      }),
      expect.objectContaining({
        key: "biz-marketing-opportunities",
        groupKey: "taishan-analysis-group",
      }),
    ]);
  });

  it("keeps detail pages as routes linked back to their list menus", () => {
    expect(marketingManifest.routes).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          key: "biz-marketing-product-solutions-detail",
          activeMenuKey: "biz-marketing-product-solutions",
        }),
        expect.objectContaining({
          key: "biz-marketing-opportunities-detail",
          activeMenuKey: "biz-marketing-opportunities",
        }),
      ]),
    );
  });
});
