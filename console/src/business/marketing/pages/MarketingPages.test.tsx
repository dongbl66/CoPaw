import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Routes, Route } from "react-router-dom";
import { renderWithProviders } from "@/test/common_setup";
import MarketingOpportunitiesPage from "./Opportunities";
import MarketingProductSolutionsPage from "./ProductSolutions";

const { mockNavigate, mockListOpportunities, mockListSavedResults } = vi.hoisted(
  () => ({
    mockNavigate: vi.fn(),
    mockListOpportunities: vi.fn(),
    mockListSavedResults: vi.fn(),
  }),
);

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/modules/marketingResult", () => ({
  marketingResultApi: {
    listOpportunities: mockListOpportunities,
    listSavedResults: mockListSavedResults,
  },
}));

describe("Marketing business pages", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockListOpportunities.mockResolvedValue({
      items: [
        {
          id: 1,
          title: "某市教育局 AI 采购项目",
          region: "济南",
          budget: 86.5,
          reason: "采购意向明确",
          summary: "建议重点跟进",
          original_link: "https://example.com/bid/2",
          created_at: "2026-05-27T00:00:00",
          updated_at: "2026-05-27T00:00:00",
        },
      ],
    });
    mockListSavedResults.mockResolvedValue({
      items: [
        {
          id: 2,
          title: "门店产品方案",
          result_type: "product",
          save_status: "saved",
          scene: "门店营销",
          summary: "适用于门店营销的方案",
          detail_content: [],
          info: {
            structuredResult: {
              eventType: "structured_result",
              version: "1.0",
              title: "门店产品方案",
              result: {
                type: "product",
                payload: {
                  title: "门店产品方案",
                  summary: "适用于门店营销的方案",
                  richText: "方案正文",
                  attachments: [],
                },
              },
            },
          },
          basic_info: {},
          product_info: { audience: "门店客户" },
          attachments: [],
          created_at: "2026-05-27T00:00:00",
          updated_at: "2026-05-27T00:00:00",
        },
      ],
    });
  });

  it("shows shared opportunity preview content and navigates to detail page", async () => {
    renderWithProviders(
      <Routes>
        <Route path="/biz/marketing/opportunities" element={<MarketingOpportunitiesPage />} />
      </Routes>,
      { initialEntries: ["/biz/marketing/opportunities"] },
    );

    expect(await screen.findByText("某市教育局 AI 采购项目")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "business.common.preview" }));

    expect(await screen.findByText("采购意向明确")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "business.common.viewDetail" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/marketing/opportunities/1");
  });

  it("shows shared product preview content and navigates to detail page", async () => {
    renderWithProviders(
      <Routes>
        <Route path="/biz/marketing/product-solutions" element={<MarketingProductSolutionsPage />} />
      </Routes>,
      { initialEntries: ["/biz/marketing/product-solutions"] },
    );

    expect(await screen.findByText("门店产品方案")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "business.common.preview" }));

    expect(await screen.findByText("方案正文")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "business.common.viewDetail" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/marketing/product-solutions/2");
  });
});
