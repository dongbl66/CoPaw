export const JSON_CODE_BLOCK_COLLAPSED_ATTR = "data-json-code-collapsed";
const JSON_CODE_BLOCK_ENHANCED_ATTR = "data-json-code-enhanced";
const STRUCTURED_JSON_NOTIFIED_ATTR = "data-structured-json-notified";
const JSON_CODE_TOGGLE_ATTR = "data-json-code-toggle";

export interface JsonCodeBlockLabels {
  viewLabel: string;
  collapseLabel: string;
}

export type StructuredJsonViewHandler = (
  structuredResult: Record<string, unknown>,
) => void;

function isJsonHeader(header: Element): boolean {
  const langNode = header.querySelector('[class*="code-header-lang"]');
  const lang = langNode?.textContent?.trim().toLowerCase() ?? "";
  return lang === "json";
}

function getWrapper(header: Element): HTMLElement | null {
  return header.closest('[class*="codeHighlighter"]');
}

function getCodeSection(wrapper: Element): HTMLElement | null {
  return wrapper.querySelector('[class*="codeHighlighter-code"]');
}

function setCollapsedState(
  wrapper: HTMLElement,
  codeSection: HTMLElement | null,
  toggleButton: HTMLButtonElement,
  labels: JsonCodeBlockLabels,
  collapsed: boolean,
) {
  wrapper.setAttribute(JSON_CODE_BLOCK_COLLAPSED_ATTR, String(collapsed));
  if (codeSection) {
    codeSection.hidden = collapsed;
    codeSection.style.display = collapsed ? "none" : "";
  }
  toggleButton.textContent = collapsed
    ? labels.viewLabel
    : labels.collapseLabel;
  toggleButton.setAttribute("aria-expanded", String(!collapsed));
}

function createToggleButton(
  wrapper: HTMLElement,
  labels: JsonCodeBlockLabels,
  onStructuredJsonView?: StructuredJsonViewHandler,
): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.setAttribute(JSON_CODE_TOGGLE_ATTR, "true");
  button.style.background = "transparent";
  button.style.border = "none";
  button.style.padding = "0";
  button.style.margin = "0";
  button.style.cursor = "pointer";
  button.style.fontSize = "12px";
  button.style.color = "inherit";
  button.style.lineHeight = "1";

  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    const codeSection = getCodeSection(wrapper);
    const isCollapsed =
      wrapper.getAttribute(JSON_CODE_BLOCK_COLLAPSED_ATTR) !== "false";

    setCollapsedState(wrapper, codeSection, button, labels, !isCollapsed);
    if (isCollapsed && codeSection && onStructuredJsonView) {
      const structuredResult = parseStructuredResult(codeSection.textContent);
      if (structuredResult) {
        onStructuredJsonView(structuredResult);
      }
    }
  });

  return button;
}

function parseStructuredResult(
  text: string | null,
): Record<string, unknown> | null {
  if (!text?.trim()) return null;

  try {
    const parsed = JSON.parse(text.trim());
    if (
      parsed &&
      typeof parsed === "object" &&
      !Array.isArray(parsed) &&
      (parsed as Record<string, unknown>).eventType === "structured_result" &&
      typeof (parsed as Record<string, unknown>).result === "object"
    ) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    return null;
  }

  return null;
}

function notifyStructuredJsonIfReady(
  wrapper: HTMLElement,
  codeSection: HTMLElement,
  onStructuredJsonView?: StructuredJsonViewHandler,
) {
  if (
    !onStructuredJsonView ||
    wrapper.getAttribute(STRUCTURED_JSON_NOTIFIED_ATTR) === "true"
  ) {
    return;
  }

  const structuredResult = parseStructuredResult(codeSection.textContent);
  if (!structuredResult) {
    return;
  }

  wrapper.setAttribute(STRUCTURED_JSON_NOTIFIED_ATTR, "true");
  onStructuredJsonView(structuredResult);
}

export function enhanceJsonCodeBlocks(
  root: ParentNode,
  labels: JsonCodeBlockLabels,
  onStructuredJsonView?: StructuredJsonViewHandler,
) {
  const headers = root.querySelectorAll('[class*="code-header"]');

  headers.forEach((header) => {
    if (!isJsonHeader(header)) return;

    const wrapper = getWrapper(header);
    const codeSection = wrapper ? getCodeSection(wrapper) : null;
    const actions = header.querySelector(
      '[class*="code-header-actions"]',
    ) as HTMLElement | null;

    if (!wrapper || !codeSection || !actions) return;

    let toggle = header.querySelector(
      `[${JSON_CODE_TOGGLE_ATTR}="true"]`,
    ) as HTMLButtonElement | null;

    if (!toggle) {
      toggle = createToggleButton(wrapper, labels, onStructuredJsonView);
      actions.prepend(toggle);
    }

    notifyStructuredJsonIfReady(wrapper, codeSection, onStructuredJsonView);

    const collapsed =
      wrapper.getAttribute(JSON_CODE_BLOCK_COLLAPSED_ATTR) !== "false";

    if (!wrapper.hasAttribute(JSON_CODE_BLOCK_ENHANCED_ATTR)) {
      wrapper.setAttribute(JSON_CODE_BLOCK_ENHANCED_ATTR, "true");
      setCollapsedState(wrapper, codeSection, toggle, labels, true);
      return;
    }

    setCollapsedState(wrapper, codeSection, toggle, labels, collapsed);
  });
}
