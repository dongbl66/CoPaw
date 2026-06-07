import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { StructuredResultEvent } from "@/pages/Chat/result-panel/types";
import FaeWorkbenchPage from "./FaeWorkbenchPage";

const { mockGetLatestUnifiedResult, mockSaveFaeResult, mockNavigate } =
  vi.hoisted(() => ({
    mockGetLatestUnifiedResult: vi.fn(),
    mockSaveFaeResult: vi.fn(),
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

vi.mock("@/api/modules/faeResult", () => ({
  faeResultApi: {
    saveResult: mockSaveFaeResult,
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
      <div data-testid="fae-result-panel">
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

function faeStructuredResult(): StructuredResultEvent {
  return {
    eventType: "structured_result",
    version: "1.0",
    title: "FAE Opportunity Report",
    result: {
      type: "government_opportunity",
      payload: {
        basicInfo: {
          projectName: "Smart City Platform",
          customerName: "City Gov",
        },
        summary: "A saved FAE opportunity result.",
      },
    },
    meta: {
      bizModule: "fae",
    },
  };
}

function faeRecord(saveStatus = "draft") {
  return {
    id: 11,
    title: "FAE Opportunity Report",
    result_type: "government_opportunity",
    save_status: saveStatus,
    scene: "government_opportunity",
    summary: "A saved FAE opportunity result.",
    info: {
      opportunityId: 99,
      structuredResult: faeStructuredResult(),
    },
    basic_info: {},
    attachments: [],
    session_id: "chat-fae",
    agent_id: "RA-agent",
    created_at: "2026-06-07T00:00:00",
    updated_at: "2026-06-07T00:01:00",
  };
}

describe("FaeWorkbenchPage", () => {
  beforeEach(() => {
    mockGetLatestUnifiedResult.mockReset();
    mockGetLatestUnifiedResult.mockResolvedValue({ item: faeRecord() });
    mockSaveFaeResult.mockReset();
    mockSaveFaeResult.mockResolvedValue(faeRecord("saved"));
    mockNavigate.mockReset();
  });

  it("loads, refreshes, saves, and emits the FAE result refresh event", async () => {
    const listRefreshHandler = vi.fn();
    window.addEventListener("fae:results-updated", listRefreshHandler);

    render(
      <FaeWorkbenchPage
        sessionId="chat-fae"
        open={true}
        refreshSignal={0}
        directResult={null}
        onOpenChange={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("fae-result-panel")).toHaveTextContent(
      "FAE Opportunity Report",
    );
    expect(mockGetLatestUnifiedResult).toHaveBeenCalledWith("chat-fae", "fae");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "refresh" }));

    await waitFor(() => {
      expect(mockGetLatestUnifiedResult).toHaveBeenCalledTimes(2);
    });
    expect(mockGetLatestUnifiedResult).toHaveBeenLastCalledWith(
      "chat-fae",
      "fae",
    );

    await user.click(screen.getByRole("button", { name: "save" }));

    await waitFor(() => {
      expect(mockSaveFaeResult).toHaveBeenCalledWith(11);
    });
    expect(listRefreshHandler).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "detail" }));
    expect(mockNavigate).toHaveBeenCalledWith("/biz/fae/results/11");

    window.removeEventListener("fae:results-updated", listRefreshHandler);
  });

  it("fetches the latest FAE record before saving when only a direct json result is visible", async () => {
    mockGetLatestUnifiedResult.mockReset();
    mockGetLatestUnifiedResult
      .mockImplementationOnce(() => new Promise(() => undefined))
      .mockResolvedValueOnce({ item: faeRecord() });

    render(
      <FaeWorkbenchPage
        sessionId="chat-fae"
        open={true}
        refreshSignal={0}
        directResult={faeStructuredResult()}
        onOpenChange={vi.fn()}
      />,
    );

    expect(await screen.findByTestId("fae-result-panel")).toHaveTextContent(
      "FAE Opportunity Report",
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "save" }));

    await waitFor(() => {
      expect(mockGetLatestUnifiedResult).toHaveBeenCalledTimes(2);
    });
    expect(mockGetLatestUnifiedResult).toHaveBeenLastCalledWith(
      "chat-fae",
      "fae",
    );

    await waitFor(() => {
      expect(mockSaveFaeResult).toHaveBeenCalledWith(11);
    });
  });
});
