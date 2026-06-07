import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, beforeEach, vi } from "vitest";
import ResultWorkbench from "./ResultWorkbench";
import {
  registerResultWorkbenchPage,
  resetResultWorkbenchPagesForTest,
} from "@/business/common/registry/resultWorkbench";

const {
  mockGetLatestMarketingResult,
  mockGetLatestFaeResult,
  mockGetLatestFraudTranscriptResult,
  mockGetLatestUnifiedResult,
  mockNavigate,
} = vi.hoisted(() => ({
  mockGetLatestMarketingResult: vi.fn(),
  mockGetLatestFaeResult: vi.fn(),
  mockGetLatestFraudTranscriptResult: vi.fn(),
  mockGetLatestUnifiedResult: vi.fn(),
  mockNavigate: vi.fn(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("../../../api/modules/marketingResult", () => ({
  marketingResultApi: {
    getLatestResult: mockGetLatestMarketingResult,
    saveResult: vi.fn(),
  },
}));

vi.mock("../../../api/modules/faeResult", () => ({
  faeResultApi: {
    getLatestResult: mockGetLatestFaeResult,
    saveResult: vi.fn(),
    createResultFromToolOutput: vi.fn(),
  },
}));

vi.mock("../../../api/modules/fraudTranscriptResult", () => ({
  fraudTranscriptResultApi: {
    getLatestResult: mockGetLatestFraudTranscriptResult,
    saveResult: vi.fn(),
  },
}));

vi.mock("../../../api/modules/unifiedResult", () => ({
  unifiedResultApi: {
    getLatestResult: mockGetLatestUnifiedResult,
  },
}));

vi.mock("./ResultPanel", () => ({
  default: ({
    open,
    result,
    onRefresh,
  }: {
    open: boolean;
    result: unknown | null;
    onRefresh: () => void;
  }) =>
    open ? (
      <div data-testid="result-panel">
        {result ? "panel-with-result" : "panel-empty"}
        <button type="button" onClick={onRefresh}>
          refresh
        </button>
      </div>
    ) : null,
}));

describe("ResultWorkbench", () => {
  beforeEach(() => {
    resetResultWorkbenchPagesForTest();
    mockGetLatestMarketingResult.mockReset();
    mockGetLatestMarketingResult.mockResolvedValue({ item: null });
    mockGetLatestFaeResult.mockReset();
    mockGetLatestFaeResult.mockResolvedValue({ item: null });
    mockGetLatestFraudTranscriptResult.mockReset();
    mockGetLatestFraudTranscriptResult.mockResolvedValue({ item: null });
    mockGetLatestUnifiedResult.mockReset();
    mockGetLatestUnifiedResult.mockResolvedValue({ item: null });
    mockNavigate.mockReset();
  });

  it("loads the registered business workbench page for the selected biz module", async () => {
    registerResultWorkbenchPage({
      bizModule: "fraud_transcript",
      Page: ({ sessionId, open }) =>
        open ? <div data-testid="fraud-workbench-page">{sessionId}</div> : null,
    });

    render(
      <ResultWorkbench
        sessionId="chat-fraud"
        defaultBizModule="fraud_transcript"
      />,
    );

    expect(await screen.findByTestId("fraud-workbench-page")).toHaveTextContent(
      "chat-fraud",
    );
    expect(mockGetLatestUnifiedResult).not.toHaveBeenCalled();
  });

  it("shows an empty panel before any session result is available", async () => {
    render(<ResultWorkbench sessionId={null} />);

    expect(await screen.findByTestId("result-panel")).toHaveTextContent(
      "panel-empty",
    );
    expect(mockGetLatestMarketingResult).not.toHaveBeenCalled();
    expect(mockGetLatestFaeResult).not.toHaveBeenCalled();
    expect(mockGetLatestFraudTranscriptResult).not.toHaveBeenCalled();
    expect(mockGetLatestUnifiedResult).not.toHaveBeenCalled();
  });

  it("shows a direct structured result before persisted polling returns", async () => {
    render(
      <ResultWorkbench
        sessionId="chat-structured"
        directResult={{
          eventType: "structured_result",
          version: "1.0",
          title: "电诈笔录分析报告",
          result: {
            type: "business",
            payload: {
              scene: "fraud_transcript_report",
              title: "电诈笔录分析报告",
            },
          },
        }}
      />,
    );

    expect(await screen.findByTestId("result-panel")).toHaveTextContent(
      "panel-with-result",
    );
  });

  it("refreshes only fraud transcript results when the active result is fraud transcript", async () => {
    mockGetLatestUnifiedResult.mockResolvedValue({
      item: {
        id: 7,
        title: "电诈笔录分析报告",
        result_type: "business",
        save_status: "draft",
        scene: "fraud_transcript_report",
        summary: "摘要",
        basic_info: {},
        product_info: {},
        qa_records: [],
        structured_result: {
          eventType: "structured_result",
          version: "1.0",
          title: "电诈笔录分析报告",
          result: {
            type: "business",
            payload: {
              scene: "fraud_transcript_report",
              title: "电诈笔录分析报告",
            },
          },
          meta: {
            bizModule: "fraud_transcript",
          },
        },
        session_id: "chat-fraud",
        agent_id: "fraud_transcript_agent",
        created_at: "2026-06-07T00:00:00",
        updated_at: "2026-06-07T00:01:00",
      },
    });

    render(
      <ResultWorkbench
        sessionId="chat-fraud"
        directResult={{
          eventType: "structured_result",
          version: "1.0",
          title: "电诈笔录分析报告",
          result: {
            type: "business",
            payload: {
              scene: "fraud_transcript_report",
              title: "电诈笔录分析报告",
            },
          },
          meta: {
            bizModule: "fraud_transcript",
          },
        }}
      />,
    );

    await waitFor(() => {
      expect(mockGetLatestUnifiedResult).toHaveBeenCalledTimes(1);
    });
    expect(mockGetLatestUnifiedResult).toHaveBeenCalledWith(
      "chat-fraud",
      "fraud_transcript",
    );
    expect(mockGetLatestMarketingResult).not.toHaveBeenCalled();
    expect(mockGetLatestFaeResult).not.toHaveBeenCalled();
    expect(mockGetLatestFraudTranscriptResult).not.toHaveBeenCalled();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "refresh" }));

    await waitFor(() => {
      expect(mockGetLatestUnifiedResult).toHaveBeenCalledTimes(2);
    });
    expect(mockGetLatestUnifiedResult).toHaveBeenLastCalledWith(
      "chat-fraud",
      "fraud_transcript",
    );
    expect(mockGetLatestMarketingResult).not.toHaveBeenCalled();
    expect(mockGetLatestFaeResult).not.toHaveBeenCalled();
    expect(mockGetLatestFraudTranscriptResult).not.toHaveBeenCalled();
  });
});
