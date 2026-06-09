import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { renderWithProviders } from "@/test/common_setup";
import GovernmentOpportunityDetailPage from "./GovernmentOpportunityDetail";
import GovernmentOpportunitiesPage from "./GovernmentOpportunities";

const { mockGetOpportunity, mockListOpportunities, mockNavigate } = vi.hoisted(() => ({
  mockGetOpportunity: vi.fn(),
  mockListOpportunities: vi.fn(),
  mockNavigate: vi.fn(),
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/modules/faeResult", () => ({
  faeResultApi: {
    getOpportunity: mockGetOpportunity,
    listOpportunities: mockListOpportunities,
  },
}));

function opportunityRecord(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    project_name: "智慧政务云平台建设项目",
    customer_name: "广州市政务服务数据管理局",
    city: "广州",
    industry: "政府",
    support_type: "技术支撑",
    create_time: "2025-11-15",
    update_time: "2026-05-20",
    requirement_desc: "本项目需要构建一个统一的政务云平台...",
    opportunity_rating: "high",
    opportunity_score: 90,
    budget_min_yuan: null,
    budget_max_yuan: null,
    budget_note: null,
    display_content: [],
    session_id: "chat-fae",
    agent_id: "RA-agent",
    ...overrides,
  };
}

describe("FAE pages", () => {
  beforeEach(() => {
    mockGetOpportunity.mockReset();
    mockGetOpportunity.mockResolvedValue(opportunityRecord());
    mockListOpportunities.mockReset();
    mockListOpportunities.mockResolvedValue({
      items: [
        opportunityRecord(),
        opportunityRecord({
          id: 2,
          project_name: "商业银行核心系统升级改造",
          customer_name: "深圳前海微众银行",
          city: "深圳",
          industry: "金融",
          support_type: "方案支撑",
          create_time: "2026-01-08",
          update_time: "2026-05-18",
          requirement_desc: "围绕核心系统升级提供专项方案支撑。",
        }),
      ],
    });
    mockNavigate.mockReset();
  });

  it("loads government opportunities from API, filters and navigates to detail", async () => {
    renderWithProviders(
      <Routes>
        <Route
          path="/biz/fae/government-opportunities"
          element={<GovernmentOpportunitiesPage />}
        />
      </Routes>,
      { initialEntries: ["/biz/fae/government-opportunities"] },
    );

    expect(screen.getByText("项目商机管理")).toBeInTheDocument();
    expect(await screen.findByText("智慧政务云平台建设项目")).toBeInTheDocument();
    expect(mockListOpportunities).toHaveBeenCalledTimes(1);
    expect(screen.getByText("共 2 个项目")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(
      screen.getByPlaceholderText("搜索项目名称、客户名称..."),
      "智慧政务云平台建设项目",
    );

    expect(screen.queryByText("商业银行核心系统升级改造")).not.toBeInTheDocument();

    await user.clear(screen.getByPlaceholderText("搜索项目名称、客户名称..."));
    await user.click(screen.getByRole("button", { name: "方案支撑" }));
    await user.click(screen.getByText("商业银行核心系统升级改造"));

    expect(mockNavigate).toHaveBeenCalledWith(
      "/biz/fae/government-opportunities/2",
    );
  });

  it("loads government opportunity detail from API and shows sections", async () => {
    mockGetOpportunity.mockResolvedValueOnce(
      opportunityRecord({
        display_content: [
          {
            type: "html",
            file_name: "智慧政务云平台建设项目_requirement_report.html",
            file_url: "/api/backend/results/fae/opportunities/1/assets/html-0",
          },
          {
            type: "pdf",
            file_name: "智慧政务云平台建设项目_requirement_report.pdf",
            file_url: "/api/backend/results/fae/opportunities/1/assets/pdf-1",
          },
        ],
      }),
    );

    renderWithProviders(
      <Routes>
        <Route
          path="/biz/fae/government-opportunities/:projectId"
          element={<GovernmentOpportunityDetailPage />}
        />
      </Routes>,
      { initialEntries: ["/biz/fae/government-opportunities/1"] },
    );

    expect(await screen.findByText("项目基本信息")).toBeInTheDocument();
    expect(mockGetOpportunity).toHaveBeenCalledWith("1");
    expect(screen.getByRole("button", { name: "返回项目列表" })).toBeInTheDocument();
    expect(screen.getByText("需求描述")).toBeInTheDocument();
    expect(screen.getByText("需求报告预览")).toBeInTheDocument();
    expect(
      screen.getByText("智慧政务云平台建设项目_requirement_report.html"),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText("本项目需要构建一个统一的政务云平台...").length,
    ).toBeGreaterThan(0);
    expect(screen.getByTitle("preview-html-智慧政务云平台建设项目_requirement_report.html")).toHaveAttribute(
      "src",
      "/api/backend/results/fae/opportunities/1/assets/html-0",
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "返回项目列表" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/fae/government-opportunities");
  });
});
