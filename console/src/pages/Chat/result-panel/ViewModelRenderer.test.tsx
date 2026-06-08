import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultRenderer } from "./ResultPanel";
import type { StructuredResultEvent } from "./types";

function buildViewModelResult(): StructuredResultEvent {
  return {
    eventType: "structured_result",
    version: "1.0",
    title: "Generic View Model",
    result: {
      type: "view_model",
      payload: {
        summary: "A generic result summary.",
        sections: [
          {
            key: "basic",
            title: "Basic",
            fields: [
              { label: "Name", value: "Project Alpha" },
              { label: "Status", value: "Active", variant: "tag", color: "green" },
            ],
          },
          {
            key: "description",
            title: "Description",
            text: "Reusable result panel content.",
          },
        ],
      },
    },
  };
}

describe("ViewModelRenderer", () => {
  it("renders generic view model summaries, fields, tags, and text sections", () => {
    render(<ResultRenderer result={buildViewModelResult()} />);

    expect(screen.getByText("A generic result summary.")).toBeInTheDocument();
    expect(screen.getByText("Basic")).toBeInTheDocument();
    expect(screen.getByText("Project Alpha")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Reusable result panel content.")).toBeInTheDocument();
  });
});
