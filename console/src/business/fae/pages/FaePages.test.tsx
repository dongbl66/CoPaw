import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { renderWithProviders } from "@/test/common_setup";
import GovernmentOpportunityDetailPage from "./GovernmentOpportunityDetail";
import GovernmentOpportunitiesPage from "./GovernmentOpportunities";

const { mockNavigate } = vi.hoisted(() => ({
  mockNavigate: vi.fn(),
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("FAE pages", () => {
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
    expect(screen.getByText("技术支撑")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(
      screen.getByPlaceholderText("搜索项目名称、客户名称..."),
      "智慧政务云平台建设项目",
    );

    expect(screen.getByText("智慧政务云平台建设项目")).toBeInTheDocument();
    expect(screen.queryByText("商业银行核心系统升级改造")).not.toBeInTheDocument();

    await user.clear(screen.getByPlaceholderText("搜索项目名称、客户名称..."));
    await user.click(screen.getByRole("button", { name: "方案支撑" }));
    await user.click(screen.getByRole("link", { name: "商业银行核心系统升级改造" }));

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
    expect(screen.getByText("项目 1 / 1")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "返回项目列表" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/fae/government-opportunities");
  });
});
