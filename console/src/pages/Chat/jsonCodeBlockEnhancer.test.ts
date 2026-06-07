import { describe, expect, it, vi } from "vitest";
import { fireEvent } from "@testing-library/react";
import {
  enhanceJsonCodeBlocks,
  JSON_CODE_BLOCK_COLLAPSED_ATTR,
} from "./jsonCodeBlockEnhancer";

function createCodeBlockDom(lang: string) {
  const root = document.createElement("div");
  root.innerHTML = `
    <div class="spark-codeHighlighter">
      <div class="spark-code-header">
        <div class="spark-code-header-lang">${lang}</div>
        <div class="spark-code-header-actions">
          <span class="spark-code-header-download">download</span>
          <span class="spark-code-header-icon">copy</span>
        </div>
      </div>
      <div class="spark-codeHighlighter-code">{"ok":true}</div>
    </div>
  `;
  return root;
}

describe("enhanceJsonCodeBlocks", () => {
  it("collapses json code blocks by default and adds a view toggle", () => {
    const root = createCodeBlockDom("json");

    enhanceJsonCodeBlocks(root, {
      viewLabel: "查看",
      collapseLabel: "收起",
    });

    const wrapper = root.querySelector(".spark-codeHighlighter");
    const code = root.querySelector(".spark-codeHighlighter-code");
    const toggle = root.querySelector(
      '[data-json-code-toggle="true"]',
    ) as HTMLButtonElement | null;

    expect(wrapper?.getAttribute(JSON_CODE_BLOCK_COLLAPSED_ATTR)).toBe("true");
    expect(code).toHaveAttribute("hidden");
    expect(code).toHaveStyle({ display: "none" });
    expect(toggle?.textContent).toBe("查看");
  });

  it("toggles json code block visibility when the view button is clicked", () => {
    const root = createCodeBlockDom("json");

    enhanceJsonCodeBlocks(root, {
      viewLabel: "查看",
      collapseLabel: "收起",
    });

    const wrapper = root.querySelector(".spark-codeHighlighter");
    const code = root.querySelector(".spark-codeHighlighter-code");
    const toggle = root.querySelector(
      '[data-json-code-toggle="true"]',
    ) as HTMLButtonElement;

    fireEvent.click(toggle);
    expect(wrapper?.getAttribute(JSON_CODE_BLOCK_COLLAPSED_ATTR)).toBe("false");
    expect(code).not.toHaveAttribute("hidden");
    expect(code).not.toHaveStyle({ display: "none" });
    expect(toggle.textContent).toBe("收起");

    fireEvent.click(toggle);
    expect(wrapper?.getAttribute(JSON_CODE_BLOCK_COLLAPSED_ATTR)).toBe("true");
    expect(code).toHaveAttribute("hidden");
    expect(toggle.textContent).toBe("查看");
  });

  it("notifies when a structured_result json block is viewed", () => {
    const root = createCodeBlockDom("json");
    const code = root.querySelector(".spark-codeHighlighter-code");
    if (code) {
      code.textContent = JSON.stringify({
        eventType: "structured_result",
        version: "1.0",
        result: {
          type: "business",
          payload: {
            scene: "fraud_transcript_report",
          },
        },
      });
    }
    const onStructuredJsonView = vi.fn();

    enhanceJsonCodeBlocks(
      root,
      {
        viewLabel: "查看",
        collapseLabel: "收起",
      },
      onStructuredJsonView,
    );

    expect(onStructuredJsonView).toHaveBeenCalledWith(
      expect.objectContaining({
        eventType: "structured_result",
        version: "1.0",
      }),
    );
    onStructuredJsonView.mockClear();

    const toggle = root.querySelector(
      '[data-json-code-toggle="true"]',
    ) as HTMLButtonElement;

    fireEvent.click(toggle);

    expect(onStructuredJsonView).toHaveBeenCalledWith(
      expect.objectContaining({
        eventType: "structured_result",
        version: "1.0",
      }),
    );
  });

  it("notifies immediately when a structured_result json block is enhanced", () => {
    const root = createCodeBlockDom("json");
    const code = root.querySelector(".spark-codeHighlighter-code");
    if (code) {
      code.textContent = JSON.stringify({
        eventType: "structured_result",
        version: "1.0",
        result: {
          type: "business",
          payload: {
            scene: "fraud_transcript_report",
          },
        },
      });
    }
    const onStructuredJsonView = vi.fn();

    enhanceJsonCodeBlocks(
      root,
      {
        viewLabel: "view",
        collapseLabel: "collapse",
      },
      onStructuredJsonView,
    );

    expect(onStructuredJsonView).toHaveBeenCalledTimes(1);
    expect(onStructuredJsonView).toHaveBeenCalledWith(
      expect.objectContaining({
        eventType: "structured_result",
        version: "1.0",
      }),
    );
  });

  it("does not change non-json code blocks", () => {
    const root = createCodeBlockDom("typescript");

    enhanceJsonCodeBlocks(root, {
      viewLabel: "查看",
      collapseLabel: "收起",
    });

    expect(root.querySelector('[data-json-code-toggle="true"]')).toBeNull();
    expect(
      root.querySelector(".spark-codeHighlighter-code"),
    ).not.toHaveAttribute("hidden");
    expect(root.querySelector(".spark-codeHighlighter-code")).not.toHaveStyle({
      display: "none",
    });
  });
});
