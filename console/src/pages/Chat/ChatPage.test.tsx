/**
 * Chat/index.tsx behavior tests
 *
 * Strategy (following the openclaw chat.test.ts pattern):
 * - Mock AgentScopeRuntimeWebUI as a spy component that captures the options prop
 * - Directly invoke callbacks like options.api.fetch and
 *   options.sender.attachments.customRequest to test ChatPage logic
 *   without depending on a real WebSocket runtime
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/common_setup";
import ChatPage from "./index";

// ---------------------------------------------------------------------------
// Capture AgentScopeRuntimeWebUI options
// ---------------------------------------------------------------------------
let capturedOptions: any = null;

const {
  mockListProviders,
  mockGetActiveModels,
  mockUploadFile,
  mockFilePreviewUrl,
  mockGetApiUrl,
  mockGetLatestMarketingResult,
  mockGetMarketingResultDetail,
  mockSaveMarketingResult,
  mockNavigate,
  mockSelectedAgent,
  mockSetSelectedAgent,
  mockGetTranscriptionProviderType,
} = vi.hoisted(() => ({
  mockListProviders: vi.fn(),
  mockGetActiveModels: vi.fn(),
  mockUploadFile: vi.fn(),
  mockFilePreviewUrl: vi.fn((f: string) => `/preview/${f}`),
  mockGetApiUrl: vi.fn((p: string) => `/api${p}`),
  mockGetLatestMarketingResult: vi.fn(),
  mockGetMarketingResultDetail: vi.fn(),
  mockSaveMarketingResult: vi.fn(),
  mockNavigate: vi.fn(),
  mockSelectedAgent: vi.fn(() => "default"),
  mockSetSelectedAgent: vi.fn(),
  mockGetTranscriptionProviderType: vi.fn(),
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("../../hooks/useAppMessage", () => ({
  useAppMessage: () => ({
    message: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  }),
}));

vi.mock("../../contexts/ApprovalContext", () => ({
  useApprovalContext: () => ({
    approvals: [] as any[],
    setApprovals: vi.fn(),
  }),
}));

vi.mock("../../plugins/PluginContext", () => ({
  usePlugins: () => ({
    plugins: [],
    registerPlugin: vi.fn(),
    toolRenderConfig: {},
  }),
  PluginContext: { Provider: ({ children }: any) => children },
}));

vi.mock("./components/ChatSessionInitializer", () => ({
  default: () => null,
}));

vi.mock("@agentscope-ai/chat", () => ({
  // render rightHeader so child components appear in the DOM
  AgentScopeRuntimeWebUI: vi.fn((props: any) => {
    capturedOptions = props.options;
    return <div data-testid="chat-ui">{props.options?.theme?.rightHeader}</div>;
  }),
  useChatAnywhereSessionsState: vi.fn(() => ({
    sessions: [],
    currentSessionId: null,
    setCurrentSessionId: vi.fn(),
    setSessions: vi.fn(),
  })),
  useChatAnywhereSessions: vi.fn(() => ({ createSession: vi.fn() })),
  useChatAnywhereInput: vi.fn(() => ({
    setLoading: vi.fn(),
    getLoading: vi.fn(),
  })),
}));

vi.mock("@/api/modules/provider", () => ({
  providerApi: {
    listProviders: mockListProviders,
    getActiveModels: mockGetActiveModels,
  },
}));

vi.mock("@/api/modules/chat", () => ({
  chatApi: {
    uploadFile: mockUploadFile,
    filePreviewUrl: mockFilePreviewUrl,
    stopChat: vi.fn(),
  },
  sessionApi: {
    getRealIdForSession: vi.fn(() => null),
    setLastUserMessage: vi.fn(),
    getSessionList: vi.fn(() => Promise.resolve([])),
  },
}));

vi.mock("@/api/modules/agent", () => ({
  agentApi: {
    getTranscriptionProviderType: mockGetTranscriptionProviderType,
  },
  TranscriptionError: class TranscriptionError extends Error {},
}));

vi.mock("@/api/modules/marketingResult", () => ({
  marketingResultApi: {
    listSavedResults: vi.fn(),
    getLatestResult: mockGetLatestMarketingResult,
    getResultDetail: mockGetMarketingResultDetail,
    saveResult: mockSaveMarketingResult,
    listOpportunities: vi.fn(),
  },
}));

vi.mock("antd", async (importOriginal) => {
  const actual = await importOriginal<typeof import("antd")>();
  return {
    ...actual,
    // Modal: do not render when open=false, avoids CSS animation leaving content in the DOM
    Modal: ({
      open,
      children,
    }: {
      open: boolean;
      children: React.ReactNode;
    }) => (open ? <div data-testid="modal">{children}</div> : null),
  };
});
vi.mock("@/api/config", () => ({
  getApiUrl: mockGetApiUrl,
  getApiToken: vi.fn(() => ""),
}));

vi.mock("@/stores/agentStore", () => ({
  useAgentStore: vi.fn(() => ({
    selectedAgent: mockSelectedAgent(),
    setSelectedAgent: mockSetSelectedAgent,
  })),
}));

vi.mock("@/contexts/ThemeContext", () => ({
  useTheme: vi.fn(() => ({ isDark: false })),
}));

vi.mock("./sessionApi", () => ({
  default: {
    onSessionIdResolved: null,
    onSessionRemoved: null,
    onSessionSelected: null,
    onSessionCreated: null,
    getRealIdForSession: vi.fn(() => null),
    setLastUserMessage: vi.fn(),
  },
}));

vi.mock("./OptionsPanel/defaultConfig", () => ({
  default: { theme: { leftHeader: {} }, api: {} },
  getDefaultConfig: vi.fn(() => ({
    theme: { leftHeader: {} },
    welcome: {},
    sender: {},
  })),
}));

vi.mock("./ModelSelector", () => ({
  default: () => <div data-testid="model-selector" />,
}));

vi.mock("./components/ChatActionGroup", () => ({
  default: () => <div data-testid="action-group" />,
}));

vi.mock("./components/ChatHeaderTitle", () => ({
  default: () => <div data-testid="header-title" />,
}));

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
const mockActiveModel = {
  active_llm: { provider_id: "openai", model: "gpt-4" },
};
const mockProviders = [
  {
    id: "openai",
    name: "OpenAI",
    models: [
      {
        id: "gpt-4",
        name: "GPT-4",
        supports_multimodal: true,
        supports_image: true,
        supports_video: false,
      },
    ],
    extra_models: [],
  },
];

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------
describe("ChatPage", () => {
  beforeEach(() => {
    capturedOptions = null;
    mockListProviders.mockResolvedValue(mockProviders);
    mockGetActiveModels.mockResolvedValue(mockActiveModel);
    mockUploadFile.mockResolvedValue({
      url: "uploaded.png",
      file_name: "uploaded.png",
    });
    mockGetTranscriptionProviderType.mockResolvedValue({
      transcription_provider_type: "disabled",
    });
    mockGetLatestMarketingResult.mockResolvedValue({ item: null });
    mockGetMarketingResultDetail.mockResolvedValue(null);
    mockSaveMarketingResult.mockResolvedValue(null);
    mockNavigate.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  // ── basic rendering ───────────────────────────────────────────────────────

  it("renders AgentScopeRuntimeWebUI", async () => {
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    expect(await screen.findByTestId("chat-ui")).toBeInTheDocument();
  });

  it("renders child components ModelSelector / ChatActionGroup / ChatHeaderTitle", async () => {
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");
    console.log("DOM:", document.body.innerHTML.substring(0, 500));
    expect(screen.getByTestId("model-selector")).toBeInTheDocument();
    expect(screen.getByTestId("action-group")).toBeInTheDocument();
    expect(screen.getByTestId("header-title")).toBeInTheDocument();
  });

  // ── customFetch: model not configured → show modal ────────────────────────

  it("customFetch returns 400 and shows modal when model is not configured", async () => {
    mockGetActiveModels.mockResolvedValue({ active_llm: undefined });
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    // directly invoke capturedOptions.api.fetch (openclaw pattern)
    const response = await capturedOptions.api.fetch({
      input: [],
      signal: undefined,
    });
    expect(response.status).toBe(400);
    expect(
      await screen.findByText("modelConfig.promptTitle"),
    ).toBeInTheDocument();
  });

  it("shows model config modal when provider API throws", async () => {
    mockGetActiveModels.mockRejectedValue(new Error("network"));
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    const response = await capturedOptions.api.fetch({
      input: [],
      signal: undefined,
    });
    expect(response.status).toBe(400);
    expect(
      await screen.findByText("modelConfig.promptTitle"),
    ).toBeInTheDocument();
  });

  // ── modal interaction ─────────────────────────────────────────────────────

  it("clicking Skip button closes the modal", async () => {
    mockGetActiveModels.mockResolvedValue({ active_llm: undefined });
    const user = userEvent.setup();
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    await capturedOptions.api.fetch({ input: [], signal: undefined });
    await screen.findByText("modelConfig.promptTitle");

    await user.click(screen.getByText("modelConfig.skipButton"));
    // antd Modal has animations; wait for DOM removal
    await waitFor(
      () =>
        expect(
          screen.queryByText("modelConfig.skipButton"),
        ).not.toBeInTheDocument(),
      { timeout: 3000 },
    );
  });

  // ── customFetch: normal send ──────────────────────────────────────────────

  it("customFetch calls /api/console/chat when model is configured", async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, status: 200 } as Response);
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    await capturedOptions.api.fetch({
      input: [{ role: "user", content: "hello" }],
      signal: undefined,
    });

    expect(fetch).toHaveBeenCalledWith(
      "/api/console/chat",
      expect.objectContaining({ method: "POST" }),
    );
  });

  // ── handleFileUpload ──────────────────────────────────────────────────────

  it("calls onError and skips upload when file exceeds 10MB", async () => {
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    const bigFile = new File([new ArrayBuffer(11 * 1024 * 1024)], "big.bin", {
      type: "application/octet-stream",
    });
    const onError = vi.fn();
    const onSuccess = vi.fn();

    await capturedOptions.sender.attachments.customRequest({
      file: bigFile,
      onSuccess,
      onError,
    });

    expect(onError).toHaveBeenCalledOnce();
    expect(mockUploadFile).not.toHaveBeenCalled();
  });

  it("uploads successfully and calls onSuccess when file is within size limit", async () => {
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    const smallFile = new File(["content"], "img.png", { type: "image/png" });
    const onSuccess = vi.fn();
    const onError = vi.fn();

    await capturedOptions.sender.attachments.customRequest({
      file: smallFile,
      onSuccess,
      onError,
      onProgress: vi.fn(),
    });

    expect(mockUploadFile).toHaveBeenCalledWith(smallFile);
    expect(onSuccess).toHaveBeenCalledWith({ url: "/preview/uploaded.png" });
    expect(onError).not.toHaveBeenCalled();
  });

  it("loads latest result into workbench without parsing chat response payload", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 1,
        title: "分析结果",
        result_type: "text",
        scene: "营销",
        summary: "这是结构化分析内容",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "分析结果",
            result: {
              type: "text",
              payload: {
                text: "这是结构化分析内容",
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-1",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-1"] });
    await screen.findByTestId("chat-ui");

    expect(mockGetLatestMarketingResult).toHaveBeenCalledWith("chat-1");
    expect(await screen.findByText("分析结果")).toBeInTheDocument();
    expect(await screen.findByText("这是结构化分析内容")).toBeInTheDocument();
  });

  it("renders business workbench content from structured result payload", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 31,
        title: "商机识别结果",
        result_type: "business",
        scene: "政府采购",
        summary: "识别到 1 条高价值商机",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "商机识别结果",
            subtitle: "政府采购",
            result: {
              type: "business",
              payload: {
                title: "商机识别结果",
                summary: "识别到 1 条高价值商机",
                opportunities: [
                  {
                    title: "某市教育局 AI 采购项目",
                    level: "A",
                    region: "济南",
                    budget: 86.5,
                    reason: "采购意向明确",
                    originalLink: "https://example.com/bid/2",
                  },
                ],
                attachments: [
                  {
                    kind: "pdf",
                    fileName: "商机报告.pdf",
                    previewUrl: "/preview/opportunities.pdf",
                  },
                ],
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-business",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-business"] });
    await screen.findByTestId("chat-ui");

    expect(await screen.findByText("识别到 1 条高价值商机")).toBeInTheDocument();
    expect(await screen.findByText("某市教育局 AI 采购项目")).toBeInTheDocument();
    expect(await screen.findByText("采购意向明确")).toBeInTheDocument();
    expect(await screen.findByText("商机报告.pdf")).toBeInTheDocument();
  });

  it("renders product workbench content from structured result payload", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 32,
        title: "产品方案",
        result_type: "product",
        scene: "门店营销",
        summary: "这里是产品方案摘要",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "产品方案",
            subtitle: "门店营销",
            result: {
              type: "product",
              payload: {
                title: "产品方案",
                summary: "这里是产品方案摘要",
                richText: "适用于门店营销的产品文案",
                attachments: [
                  {
                    kind: "pdf",
                    fileName: "产品方案.pdf",
                    previewUrl: "/preview/product-plan.pdf",
                  },
                ],
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-product",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-product"] });
    await screen.findByTestId("chat-ui");

    expect(await screen.findByText("这里是产品方案摘要")).toBeInTheDocument();
    expect(await screen.findByText("适用于门店营销的产品文案")).toBeInTheDocument();
    expect(await screen.findByText("产品方案.pdf")).toBeInTheDocument();
  });

  it("saves the current result from the workbench action area", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 41,
        title: "待保存方案",
        result_type: "product",
        save_status: "draft",
        scene: "门店营销",
        summary: "待保存摘要",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "待保存方案",
            result: {
              type: "product",
              payload: {
                title: "待保存方案",
                summary: "待保存摘要",
                attachments: [],
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-save",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });
    mockSaveMarketingResult.mockResolvedValue({
      id: 41,
      title: "待保存方案",
      result_type: "product",
      save_status: "saved",
      scene: "门店营销",
      summary: "待保存摘要",
      detail_content: [],
      info: {
        structuredResult: {
          eventType: "structured_result",
          version: "1.0",
          title: "待保存方案",
          result: {
            type: "product",
            payload: {
              title: "待保存方案",
              summary: "待保存摘要",
              attachments: [],
            },
          },
        },
      },
      basic_info: {},
      product_info: {},
      attachments: [],
      session_id: "chat-save",
      agent_id: "market_agent",
      created_at: "2026-05-27T00:00:00",
      updated_at: "2026-05-27T00:01:00",
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-save"] });
    await screen.findByText("待保存方案");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "chat.resultPanel.save" }));

    expect(mockSaveMarketingResult).toHaveBeenCalledWith(41);
  });

  it("polls latest result for the active session", async () => {
    vi.useFakeTimers();
    mockGetLatestMarketingResult.mockResolvedValue({ item: null });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-2"] });
    await screen.findByTestId("chat-ui");

    expect(mockGetLatestMarketingResult).toHaveBeenCalledTimes(1);
    expect(mockGetLatestMarketingResult).toHaveBeenCalledWith("chat-2");

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(mockGetLatestMarketingResult).toHaveBeenCalledTimes(2);
  });

  it("refreshes latest result when refresh button is clicked", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 11,
        title: "可刷新结果",
        result_type: "text",
        scene: "营销",
        summary: "刷新前内容",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "可刷新结果",
            result: {
              type: "text",
              payload: {
                text: "刷新前内容",
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-3",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-3"] });
    await screen.findByText("可刷新结果");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "chat.resultPanel.refresh" }));

    expect(mockGetLatestMarketingResult).toHaveBeenCalledTimes(2);
    expect(mockGetLatestMarketingResult).toHaveBeenLastCalledWith("chat-3");
  });

  it("navigates to product detail page when detail button is clicked", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 21,
        title: "结果详情",
        result_type: "product",
        scene: "营销",
        summary: "摘要",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "结果详情",
            result: {
              type: "product",
              payload: {
                title: "结果详情",
                summary: "摘要",
                attachments: [],
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-4",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-4"] });
    await screen.findByText("结果详情");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "chat.resultPanel.viewDetail" }));

    expect(mockNavigate).toHaveBeenCalledWith("/biz/marketing/product-solutions/21");
  });

  it("marks current result as saved when save button is clicked", async () => {
    mockGetLatestMarketingResult.mockResolvedValue({
      item: {
        id: 41,
        title: "待保存结果",
        result_type: "text",
        summary: "待保存摘要",
        detail_content: [],
        info: {
          structuredResult: {
            eventType: "structured_result",
            version: "1.0",
            title: "待保存结果",
            result: {
              type: "text",
              payload: {
                text: "待保存摘要",
              },
            },
          },
        },
        basic_info: {},
        product_info: {},
        attachments: [],
        session_id: "chat-5",
        agent_id: "market_agent",
        created_at: "2026-05-27T00:00:00",
        updated_at: "2026-05-27T00:00:00",
      },
    });
    mockSaveMarketingResult.mockResolvedValue({
      id: 41,
      title: "待保存结果",
      result_type: "text",
      save_status: "saved",
      summary: "待保存摘要",
      detail_content: [],
      info: {
        structuredResult: {
          eventType: "structured_result",
          version: "1.0",
          title: "待保存结果",
          result: {
            type: "text",
            payload: {
              text: "待保存摘要",
            },
          },
        },
      },
      basic_info: {},
      product_info: {},
      attachments: [],
      session_id: "chat-5",
      agent_id: "market_agent",
      created_at: "2026-05-27T00:00:00",
      updated_at: "2026-05-27T00:01:00",
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat/chat-5"] });
    await screen.findByText("待保存结果");

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "chat.resultPanel.save" }));

    expect(mockSaveMarketingResult).toHaveBeenCalledWith(41);
  });

  // ── voice input mode ───────────────────────────────────────────────────────

  it("does not enable browser speech before transcription provider type loads", async () => {
    let resolveProviderType!: (value: {
      transcription_provider_type: string;
    }) => void;
    mockGetTranscriptionProviderType.mockReturnValue(
      new Promise((resolve) => {
        resolveProviderType = resolve;
      }),
    );

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    expect(capturedOptions.sender.allowSpeech).toBe(false);
    expect(capturedOptions.sender.prefix).toBeUndefined();

    act(() => {
      resolveProviderType({ transcription_provider_type: "disabled" });
    });
  });

  it("uses Whisper speech button and disables browser speech when transcription provider is enabled", async () => {
    mockGetTranscriptionProviderType.mockResolvedValue({
      transcription_provider_type: "whisper_api",
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    await waitFor(() => {
      expect(capturedOptions.sender.allowSpeech).toBe(false);
      expect(capturedOptions.sender.prefix).toBeTruthy();
    });
  });

  it("keeps browser speech enabled when transcription provider is disabled", async () => {
    mockGetTranscriptionProviderType.mockResolvedValue({
      transcription_provider_type: "disabled",
    });

    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");

    await waitFor(() => {
      expect(capturedOptions.sender.allowSpeech).toBe(true);
      expect(capturedOptions.sender.prefix).toBeUndefined();
    });
  });

  // ── multimodal caps ───────────────────────────────────────────────────────

  it("calls providerApi on mount to fetch multimodal capabilities", async () => {
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");
    await waitFor(() => expect(mockGetActiveModels).toHaveBeenCalled());
    expect(mockListProviders).toHaveBeenCalled();
  });

  it("model-switched event triggers re-fetch of multimodal capabilities", async () => {
    renderWithProviders(<ChatPage />, { initialEntries: ["/chat"] });
    await screen.findByTestId("chat-ui");
    // wait for initial mount calls to settle
    await waitFor(() => expect(mockGetActiveModels).toHaveBeenCalled());
    const callsBefore = mockGetActiveModels.mock.calls.length;

    act(() => {
      window.dispatchEvent(new CustomEvent("model-switched"));
    });

    await waitFor(() =>
      expect(mockGetActiveModels.mock.calls.length).toBeGreaterThan(
        callsBefore,
      ),
    );
  });
});
