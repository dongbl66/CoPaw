import { render, screen } from "@testing-library/react";
import { describe, expect, it, beforeEach, vi } from "vitest";
import ResultWorkbench from "./ResultWorkbench";

const { mockGetLatestResult, mockNavigate } = vi.hoisted(() => ({
  mockGetLatestResult: vi.fn(),
  mockNavigate: vi.fn(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("../../../api/modules/marketingResult", () => ({
  marketingResultApi: {
    getLatestResult: mockGetLatestResult,
    saveResult: vi.fn(),
  },
}));

vi.mock("./ResultPanel", () => ({
  default: ({
    open,
    result,
  }: {
    open: boolean;
    result: unknown | null;
  }) =>
    open ? (
      <div data-testid="result-panel">
        {result ? "panel-with-result" : "panel-empty"}
      </div>
    ) : null,
}));

describe("ResultWorkbench", () => {
  beforeEach(() => {
    mockGetLatestResult.mockReset();
    mockGetLatestResult.mockResolvedValue({ item: null });
    mockNavigate.mockReset();
  });

  it("shows an empty panel before any session result is available", async () => {
    render(<ResultWorkbench sessionId={null} />);

    expect(await screen.findByTestId("result-panel")).toHaveTextContent(
      "panel-empty",
    );
    expect(mockGetLatestResult).not.toHaveBeenCalled();
  });
});
