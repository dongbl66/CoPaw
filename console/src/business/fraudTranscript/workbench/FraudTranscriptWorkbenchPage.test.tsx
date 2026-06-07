import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import FraudTranscriptWorkbenchPage from "./FraudTranscriptWorkbenchPage";

const {
  mockGetLatestUnifiedResult,
  mockSaveFraudTranscriptResult,
  mockNavigate,
} = vi.hoisted(() => ({
  mockGetLatestUnifiedResult: vi.fn(),
  mockSaveFraudTranscriptResult: vi.fn(),
  mockNavigate: vi.fn(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("@/api/modules/unifiedResult", () => ({
  unifiedResultApi: {
    getLatestResult: mockGetLatestUnifiedResult,
  },
}));

vi.mock("@/api/modules/fraudTranscriptResult", () => ({
  fraudTranscriptResultApi: {
    saveResult: mockSaveFraudTranscriptResult,
  },
}));

vi.mock("@/pages/Chat/result-panel/ResultPanel", () => ({
  default: ({
    open,
    result,
    onRefresh,
    onSave,
    onViewDetail,
    showViewDetail,
  }: {
    open: boolean;
    result: { title?: string } | null;
    onRefresh?: () => void;
    onSave?: () => void;
    onViewDetail?: () => void;
    showViewDetail?: boolean;
  }) =>
    open ? (
      <div data-testid="fraud-result-panel">
        <span>{result?.title || "empty"}</span>
        <button type="button" onClick={onRefresh}>
          refresh
        </button>
        <button type="button" onClick={onSave}>
          save
        </button>
        {showViewDetail ? (
          <button type="button" onClick={onViewDetail}>
            detail
          </button>
        ) : null}
      </div>
    ) : null,
}));

function fraudRecord(saveStatus = "draft") {
  return {
    id: 7,
    title: "电诈笔录分析报告",
    result_type: "business",
    save_status: saveStatus,
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
  };
}

describe("FraudTranscriptWorkbenchPage", () => {
  beforeEach(() => {
    mockGetLatestUnifiedResult.mockReset();
    mockGetLatestUnifiedResult.mockResolvedValue({ item: fraudRecord() });
    mockSaveFraudTranscriptResult.mockReset();
    mockSaveFraudTranscriptResult.mockResolvedValue(fraudRecord("saved"));
    mockNavigate.mockReset();
  });

  it("loads, refreshes, saves, and emits the fraud transcript list refresh event", async () => {
    const listRefreshHandler = vi.fn();
    window.addEventListener(
      "fraud-transcript:results-updated",
      listRefreshHandler,
    );

    render(
      <FraudTranscriptWorkbenchPage
        sessionId="chat-fraud"
        open={true}
        refreshSignal={0}
        directResult={null}
        onOpenChange={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("fraud-result-panel")).toHaveTextContent(
      "电诈笔录分析报告",
    );
    expect(mockGetLatestUnifiedResult).toHaveBeenCalledWith(
      "chat-fraud",
      "fraud_transcript",
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "refresh" }));

    await waitFor(() => {
      expect(mockGetLatestUnifiedResult).toHaveBeenCalledTimes(2);
    });
    expect(mockGetLatestUnifiedResult).toHaveBeenLastCalledWith(
      "chat-fraud",
      "fraud_transcript",
    );

    await user.click(screen.getByRole("button", { name: "save" }));

    await waitFor(() => {
      expect(mockSaveFraudTranscriptResult).toHaveBeenCalledWith(7);
    });
    expect(listRefreshHandler).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "detail" }));
    expect(mockNavigate).toHaveBeenCalledWith("/biz/fraud-transcript/results/7");

    window.removeEventListener(
      "fraud-transcript:results-updated",
      listRefreshHandler,
    );
  });

  it("fetches the latest fraud record before saving when only a direct json result is visible", async () => {
    mockGetLatestUnifiedResult.mockReset();
    mockGetLatestUnifiedResult
      .mockImplementationOnce(() => new Promise(() => undefined))
      .mockResolvedValueOnce({ item: fraudRecord() });

    render(
      <FraudTranscriptWorkbenchPage
        sessionId="chat-fraud"
        open={true}
        refreshSignal={0}
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
        onOpenChange={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("fraud-result-panel")).toHaveTextContent(
      "电诈笔录分析报告",
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "save" }));

    await waitFor(() => {
      expect(mockGetLatestUnifiedResult).toHaveBeenCalledTimes(2);
    });
    expect(mockGetLatestUnifiedResult).toHaveBeenLastCalledWith(
      "chat-fraud",
      "fraud_transcript",
    );

    await waitFor(() => {
      expect(mockSaveFraudTranscriptResult).toHaveBeenCalledWith(7);
    });
  });
});
