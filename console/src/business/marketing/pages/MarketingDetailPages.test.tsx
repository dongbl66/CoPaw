import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { renderWithProviders } from "@/test/common_setup";
import MarketingOpportunityDetailPage from "./OpportunityDetail";
import MarketingProductSolutionDetailPage from "./ProductSolutionDetail";

const { mockGetOpportunityDetail, mockGetResultDetail, mockNavigate } = vi.hoisted(
  () => ({
    mockGetOpportunityDetail: vi.fn(),
    mockGetResultDetail: vi.fn(),
    mockNavigate: vi.fn(),
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
    getOpportunityDetail: mockGetOpportunityDetail,
    getResultDetail: mockGetResultDetail,
  },
}));

describe("Marketing detail pages", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockGetOpportunityDetail.mockResolvedValue({
      id: 1,
      title: "某市教育局 AI 采购项目",
      region: "济南",
      budget: 86.5,
      reason: "采购意向明确",
      summary: "建议重点跟进",
      original_link: "https://example.com/bid/2",
      created_at: "2026-05-27T00:00:00",
      updated_at: "2026-05-27T00:00:00",
    });
    mockGetResultDetail.mockResolvedValue({
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
    });
  });

  it("renders opportunity detail with shared business content", async () => {
    renderWithProviders(
      <Routes>
        <Route
          path="/biz/marketing/opportunities/:opportunityId"
          element={<MarketingOpportunityDetailPage />}
        />
      </Routes>,
      { initialEntries: ["/biz/marketing/opportunities/1"] },
    );

    expect(await screen.findByText("某市教育局 AI 采购项目")).toBeInTheDocument();
    expect(await screen.findByText("采购意向明确")).toBeInTheDocument();
  });

  it("renders product detail with shared product content", async () => {
    renderWithProviders(
      <Routes>
        <Route
          path="/biz/marketing/product-solutions/:resultId"
          element={<MarketingProductSolutionDetailPage />}
        />
      </Routes>,
      { initialEntries: ["/biz/marketing/product-solutions/2"] },
    );

    expect(await screen.findByText("门店产品方案")).toBeInTheDocument();
    expect(await screen.findByText("方案正文")).toBeInTheDocument();
  });
});
