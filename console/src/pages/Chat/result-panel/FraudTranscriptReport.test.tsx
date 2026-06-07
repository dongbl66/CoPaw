import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultRenderer } from "./ResultPanel";
import type { StructuredResultEvent } from "./types";

function buildFraudResult(): StructuredResultEvent {
  return {
    eventType: "structured_result",
    version: "1.0",
    title: "电诈笔录分析报告",
    result: {
      type: "business",
      payload: {
        title: "电诈笔录分析报告",
        summary: "受害人通过微信群接触诈骗人员。",
        scene: "fraud_transcript_report",
        basicInfo: {
          姓名: "张三",
          联系方式: "13800000000",
          涉案金额: "50000",
        },
        productInfo: {
          诈骗路径: "微信群接触 -> 下载 APP -> 转账",
          风险等级: "高",
          质量评分: 82,
          缺失项: ["APP 下载来源"],
        },
        opportunities: [
          {
            title: "问题：你是如何接触到对方的？",
            level: "已回答",
            type: "模板问答",
            summary: "通过微信群接触对方。",
            reason: "接触渠道已明确。",
          },
        ],
        attachments: [],
      },
    },
    meta: {
      bizModule: "fraud_transcript",
    },
  };
}

describe("FraudTranscriptReport", () => {
  it("renders fraud transcript sections from a business structured result", () => {
    render(<ResultRenderer result={buildFraudResult()} />);

    expect(screen.getByText("基本信息")).toBeInTheDocument();
    expect(screen.getByText("诈骗路径分析")).toBeInTheDocument();
    expect(screen.getByText("问题及答案")).toBeInTheDocument();
    expect(screen.getByText("质量评估")).toBeInTheDocument();
    expect(screen.getByText("张三")).toBeInTheDocument();
    expect(screen.getByText("问题：你是如何接触到对方的？")).toBeInTheDocument();
    expect(screen.getByText("APP 下载来源")).toBeInTheDocument();
  });
});
