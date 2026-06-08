import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultRenderer } from "./ResultPanel";
import type { StructuredResultEvent } from "./types";

function buildSnakeCaseFaeResult(): StructuredResultEvent {
  return {
    eventType: "structured_result",
    version: "1.0",
    title: "FAE 政企商机分析报告",
    result: {
      type: "government_opportunity",
      payload: {
        scene: "government_opportunity",
        output: "识别到高价值商机：公安笔录智能评估项目",
        project_name: "公安笔录智能评估与要素提取系统",
        customer_name: "某省公安厅",
        city: "",
        industry: "公安/政法",
        support_type: "综合支撑",
        requirement_desc: "建设笔录规范性自动评估、涉诈要素提取和 RPA 自动调证能力。",
        opportunity_rating: "medium",
        opportunity_score: 75,
        budget: {
          min_yuan: null,
          max_yuan: null,
          note: "材料未体现预算信息",
        },
        display_content: [],
      },
    },
    meta: {
      bizModule: "fae",
      source: "skill",
    },
  };
}

describe("GovernmentOpportunityRenderer", () => {
  it("renders snake_case FAE structured_result payloads", () => {
    render(<ResultRenderer result={buildSnakeCaseFaeResult()} />);

    expect(screen.getByText("公安笔录智能评估与要素提取系统")).toBeInTheDocument();
    expect(screen.getByText("某省公安厅")).toBeInTheDocument();
    expect(screen.getByText("公安/政法")).toBeInTheDocument();
    expect(screen.getByText("综合支撑")).toBeInTheDocument();
    expect(
      screen.getByText("建设笔录规范性自动评估、涉诈要素提取和 RPA 自动调证能力。"),
    ).toBeInTheDocument();
    expect(screen.getByText("75/100", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("待核实 - 待核实", { exact: false })).toBeInTheDocument();
  });
});
