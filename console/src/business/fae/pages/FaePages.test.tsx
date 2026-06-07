import { beforeEach, describe, expect, it, vi } from "vitest";
import { waitFor } from "@testing-library/react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { renderWithProviders } from "@/test/common_setup";
import FaeResultDetailPage from "./ResultDetail";
import FaeResultsPage from "./Results";
import GovernmentOpportunityDetailPage from "./GovernmentOpportunityDetail";
import GovernmentOpportunitiesPage from "./GovernmentOpportunities";

const { mockGetFaeResultDetail, mockListFaeResults, mockNavigate } = vi.hoisted(() => ({
  mockGetFaeResultDetail: vi.fn(),
  mockListFaeResults: vi.fn(),
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
    getResultDetail: mockGetFaeResultDetail,
    listResults: mockListFaeResults,
  },
}));

function faeResultRecord(saveStatus = "saved") {
  return {
    id: 11,
    title: "FAE Opportunity Report",
    result_type: "government_opportunity",
    save_status: saveStatus,
    scene: "government_opportunity",
    summary: "A saved FAE opportunity result.",
    info: {
      opportunityId: 99,
      structuredResult: {
        eventType: "structured_result",
        version: "1.0",
        title: "FAE Opportunity Report",
        result: {
          type: "government_opportunity",
          payload: {
            basicInfo: {
              projectName: "Smart City Platform",
              customerName: "City Gov",
              city: "Hangzhou",
              industry: "Government",
              supportType: "Solution",
            },
            summary: "A saved FAE opportunity result.",
          },
        },
        meta: {
          bizModule: "fae",
        },
      },
    },
    basic_info: {},
    attachments: [],
    session_id: "chat-fae",
    agent_id: "RA-agent",
    created_at: "2026-06-07T00:00:00",
    updated_at: "2026-06-07T00:01:00",
  };
}

describe("FAE pages", () => {
  beforeEach(() => {
    mockGetFaeResultDetail.mockReset();
    mockGetFaeResultDetail.mockResolvedValue(faeResultRecord());
    mockListFaeResults.mockReset();
    mockListFaeResults.mockResolvedValue({ items: [faeResultRecord()] });
    mockNavigate.mockReset();
  });

  it("shows saved FAE results, reloads after save events, and navigates to detail", async () => {
    renderWithProviders(
      <Routes>
        <Route path="/biz/fae/results" element={<FaeResultsPage />} />
      </Routes>,
      { initialEntries: ["/biz/fae/results"] },
    );

    expect(await screen.findByText("FAE Opportunity Report")).toBeInTheDocument();
    expect(mockListFaeResults).toHaveBeenCalledWith(true);

    window.dispatchEvent(new CustomEvent("fae:results-updated"));

    await waitFor(() => {
      expect(mockListFaeResults).toHaveBeenCalledTimes(2);
    });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "View Detail" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/fae/results/11");
  });

  it("shows a saved FAE result detail page", async () => {
    renderWithProviders(
      <Routes>
        <Route path="/biz/fae/results/:resultId" element={<FaeResultDetailPage />} />
      </Routes>,
      { initialEntries: ["/biz/fae/results/11"] },
    );

    expect(await screen.findByText("FAE Opportunity Report")).toBeInTheDocument();
    expect(screen.getByText("Smart City Platform")).toBeInTheDocument();
    expect(mockGetFaeResultDetail).toHaveBeenCalledWith("11");
  });

  it("shows government opportunity list stats, filters and navigates to detail", async () => {
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
    expect(screen.getByText("共 8 个项目")).toBeInTheDocument();
    expect(screen.getByText("活跃商机")).toBeInTheDocument();
    expect(screen.getAllByText("技术支撑").length).toBeGreaterThan(0);

    const user = userEvent.setup();
    await user.type(
      screen.getByPlaceholderText("搜索项目名称、客户名称..."),
      "智慧政务云平台建设项目",
    );

    expect(screen.getByText("智慧政务云平台建设项目")).toBeInTheDocument();
    expect(screen.queryByText("商业银行核心系统升级改造")).not.toBeInTheDocument();

    await user.clear(screen.getByPlaceholderText("搜索项目名称、客户名称..."));
    await user.click(screen.getByRole("button", { name: "方案支撑" }));
    await user.click(screen.getByText("商业银行核心系统升级改造"));

    expect(mockNavigate).toHaveBeenCalledWith(
      "/biz/fae/government-opportunities/2",
    );
  });

  it("shows government opportunity detail sections and pdf preview", async () => {
    renderWithProviders(
      <Routes>
        <Route
          path="/biz/fae/government-opportunities/:projectId"
          element={<GovernmentOpportunityDetailPage />}
        />
      </Routes>,
      { initialEntries: ["/biz/fae/government-opportunities/1"] },
    );

    expect(screen.getByRole("button", { name: "返回项目列表" })).toBeInTheDocument();
    expect(screen.getByText("项目基本信息")).toBeInTheDocument();
    expect(screen.getByText("需求描述")).toBeInTheDocument();
    expect(screen.getByText("需求文档（PDF预览）")).toBeInTheDocument();
    expect(screen.getByText("智慧政务云平台建设项目需求规格说明书")).toBeInTheDocument();
    expect(screen.getByText("本项目需要构建一个统一的政务云平台...")).toBeInTheDocument();
    expect(screen.getByText(/项目 1 \/ 1/)).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "返回项目列表" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/fae/government-opportunities");
  });
});
