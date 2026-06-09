import type {
  StructuredResultEvent,
  StructuredViewModelField,
  StructuredWorkbenchAttachment,
} from "@/pages/Chat/result-panel/types";

interface GovernmentOpportunityPayload {
  summary?: string;
  output?: string;
  project_name?: string;
  customer_name?: string;
  city?: string;
  industry?: string;
  support_type?: string;
  requirement_desc?: string;
  opportunity_rating?: "high" | "medium" | "low" | string;
  opportunity_score?: number;
  basicInfo?: {
    projectName?: string;
    customerName?: string;
    city?: string;
    industry?: string;
    supportType?: string;
  };
  requirementDesc?: string;
  opportunityRating?: "high" | "medium" | "low" | string;
  opportunityScore?: number;
  budget?: {
    minYuan?: number | null;
    maxYuan?: number | null;
    min_yuan?: number | null;
    max_yuan?: number | null;
    note?: string;
  };
  attachments?: StructuredWorkbenchAttachment[];
  display_content?: Array<{
    type?: string;
    file_name?: string;
    fileName?: string;
    file_url?: string;
    fileUrl?: string;
    file_path?: string;
    filePath?: string;
    asset_id?: string;
    assetId?: string;
  }>;
}

const OPPORTUNITY_RATING_COLORS: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "blue",
};

const OPPORTUNITY_RATING_LABELS: Record<string, string> = {
  high: "高价值",
  medium: "中等价值",
  low: "低价值",
};

function normalizeAttachments(
  payload: GovernmentOpportunityPayload,
): StructuredWorkbenchAttachment[] {
  return (
    payload.attachments ??
    payload.display_content?.map((item) => ({
      kind: (item.type || "file") as "pdf" | "html" | "web" | "image" | "file",
      fileName: item.fileName ?? item.file_name,
      fileUrl: item.fileUrl ?? item.file_url,
      filePath: item.filePath ?? item.file_path,
      extra: {
        asset_id: item.assetId ?? item.asset_id,
      },
    })) ??
    []
  );
}

function normalizeBudget(payload: GovernmentOpportunityPayload): string {
  const budget = payload.budget;
  if (!budget) {
    return "待核实";
  }

  const minYuan = budget.minYuan ?? budget.min_yuan ?? null;
  const maxYuan = budget.maxYuan ?? budget.max_yuan ?? null;
  const minText = typeof minYuan === "number" ? `¥${minYuan.toLocaleString()}` : "待核实";
  const maxText = typeof maxYuan === "number" ? `¥${maxYuan.toLocaleString()}` : "待核实";
  return `${minText} - ${maxText}${budget.note ? `（${budget.note}）` : ""}`;
}

function field(label: string, value: unknown): StructuredViewModelField {
  return {
    label,
    value: typeof value === "string" || typeof value === "number" ? value : "",
  };
}

export function adaptGovernmentOpportunityResult(
  result: StructuredResultEvent,
): StructuredResultEvent | null {
  if (result.result.type !== "government_opportunity") {
    return null;
  }

  const payload = result.result.payload as GovernmentOpportunityPayload;
  const rating = payload.opportunityRating ?? payload.opportunity_rating;
  const opportunityScore = payload.opportunityScore ?? payload.opportunity_score;
  const requirementDesc = payload.requirementDesc ?? payload.requirement_desc;
  const attachments = normalizeAttachments(payload);

  const sections = [
    {
      key: "basic-info",
      title: "基本信息",
      fields: [
        field("项目名称", payload.basicInfo?.projectName ?? payload.project_name),
        field("客户名称", payload.basicInfo?.customerName ?? payload.customer_name),
        field("城市", payload.basicInfo?.city ?? payload.city),
        field("行业", payload.basicInfo?.industry ?? payload.industry),
        {
          label: "支撑类型",
          value: payload.basicInfo?.supportType ?? payload.support_type ?? "",
          variant: "tag" as const,
          color: "processing",
        },
      ],
    },
    {
      key: "opportunity-score",
      title: "商机研判",
      fields: [
        {
          label: "商机评级",
          value: rating ? OPPORTUNITY_RATING_LABELS[rating] ?? rating : "",
          variant: "tag" as const,
          color: rating ? OPPORTUNITY_RATING_COLORS[rating] ?? "default" : "default",
        },
        field(
          "评分",
          typeof opportunityScore === "number" ? `${opportunityScore}/100` : "",
        ),
        field("预算区间", normalizeBudget(payload)),
      ],
    },
    ...(requirementDesc
      ? [
          {
            key: "requirement-desc",
            title: "需求描述",
            text: requirementDesc,
          },
        ]
      : []),
    ...(attachments.length > 0
      ? [
          {
            key: "attachments",
            title: "附件",
            attachments,
          },
        ]
      : []),
  ];

  return {
    ...result,
    result: {
      type: "view_model",
      payload: {
        summary: payload.summary ?? payload.output,
        sections,
      },
    },
  };
}
