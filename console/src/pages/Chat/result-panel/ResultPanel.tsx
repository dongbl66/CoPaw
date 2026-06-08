import { Button, Empty, Space, Table, Typography, Tag, Descriptions, Card } from "antd";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  BusinessDetailContent,
  ProductSolutionDetailContent,
} from "@/business/marketing/components/detailContent";
import FraudTranscriptReport from "./FraudTranscriptReport";
import { openExternalLink } from "../../../utils/openExternalLink";
import { copyText } from "../utils";
import { resolvePdfDisplayUrl } from "./utils";
import type {
  StructuredBusinessPayload,
  StructuredActionsPayload,
  StructuredHtmlPayload,
  StructuredPdfPayload,
  StructuredProductPayload,
  StructuredResultAction,
  StructuredResultEvent,
  StructuredTablePayload,
  StructuredTextPayload,
  StructuredWebPayload,
  GovernmentOpportunityPayload,
} from "./types";
import styles from "../index.module.less";

const { Paragraph, Text, Title } = Typography;

function TextRenderer({ payload }: { payload: StructuredTextPayload }) {
  if (payload.markdown) {
    return (
      <div className={styles.resultMarkdown}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {payload.text}
        </ReactMarkdown>
      </div>
    );
  }

  return (
    <Paragraph className={styles.resultPlainText}>{payload.text}</Paragraph>
  );
}

function BusinessRenderer({ payload }: { payload: StructuredBusinessPayload }) {
  if (payload.scene === "fraud_transcript_report") {
    return <FraudTranscriptReport payload={payload} />;
  }

  return <BusinessDetailContent payload={payload} mode="panel" />;
}

function ProductRenderer({ payload }: { payload: StructuredProductPayload }) {
  return <ProductSolutionDetailContent payload={payload} mode="panel" />;
}

function WebRenderer({ payload }: { payload: StructuredWebPayload }) {
  return (
    <iframe
      src={payload.url}
      title="result-web-view"
      className={styles.resultFrame}
      sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
    />
  );
}

function PdfRenderer({ payload }: { payload: StructuredPdfPayload }) {
  const { t } = useTranslation();
  const url = resolvePdfDisplayUrl(payload);
  if (!url) {
    return <Empty description={t("chat.resultPanel.emptyPdf")} />;
  }

  return (
    <embed
      src={url}
      type="application/pdf"
      className={styles.resultFrame}
      title={payload.fileName || "pdf-preview"}
    />
  );
}

function HtmlRenderer({ payload }: { payload: StructuredHtmlPayload }) {
  const { t } = useTranslation();
  if (payload.url) {
    return (
      <iframe
        src={payload.url}
        title="result-html-view"
        className={styles.resultFrame}
        sandbox="allow-same-origin allow-scripts allow-forms"
      />
    );
  }

  if (!payload.html) {
    return <Empty description={t("chat.resultPanel.emptyHtml")} />;
  }

  return (
    <iframe
      srcDoc={payload.html}
      title="result-html-doc"
      className={styles.resultFrame}
      sandbox="allow-same-origin"
    />
  );
}

function TableRenderer({ payload }: { payload: StructuredTablePayload }) {
  const columns = payload.columns.map((column) => ({
    title: column.title,
    key: column.key,
    dataIndex: column.dataIndex ?? column.key,
  }));

  return (
    <Table
      size="small"
      bordered
      rowKey={(_, index) => `${index ?? 0}`}
      columns={columns}
      dataSource={payload.rows}
      pagination={false}
      scroll={{ x: "max-content", y: 420 }}
    />
  );
}

async function handleActionClick(action: StructuredResultAction) {
  if (action.actionType === "open_url") {
    const url = String(action.payload?.url || "");
    if (url) {
      openExternalLink(url);
    }
    return;
  }

  if (action.actionType === "download") {
    const url = String(action.payload?.url || "");
    if (url) {
      openExternalLink(url);
    }
    return;
  }

  if (action.actionType === "copy") {
    const text = String(action.payload?.text || "");
    if (text) {
      await copyText(text);
    }
    return;
  }

  if (action.actionType === "emit_event") {
    window.dispatchEvent(
      new CustomEvent("chat-result-panel-action", {
        detail: action.payload ?? {},
      }),
    );
  }
}

function ActionsRenderer({ payload }: { payload: StructuredActionsPayload }) {
  return (
    <Space wrap>
      {payload.actions.map((action) => (
        <Button
          key={action.key}
          onClick={() => {
            void handleActionClick(action);
          }}
        >
          {action.label}
        </Button>
      ))}
    </Space>
  );
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

function normalizeGovernmentOpportunityPayload(
  payload: GovernmentOpportunityPayload,
) {
  const budget = payload.budget;
  const attachments =
    payload.attachments ??
    payload.display_content?.map((item) => ({
      kind: (item.type || "file") as "pdf" | "html" | "web" | "image" | "file",
      fileName: item.fileName ?? item.file_name,
      fileUrl: item.fileUrl ?? item.file_url,
      filePath: item.filePath ?? item.file_path,
    })) ??
    [];

  return {
    summary: payload.summary ?? payload.output,
    basicInfo: {
      projectName: payload.basicInfo?.projectName ?? payload.project_name,
      customerName: payload.basicInfo?.customerName ?? payload.customer_name,
      city: payload.basicInfo?.city ?? payload.city,
      industry: payload.basicInfo?.industry ?? payload.industry,
      supportType: payload.basicInfo?.supportType ?? payload.support_type,
    },
    requirementDesc: payload.requirementDesc ?? payload.requirement_desc,
    opportunityRating:
      payload.opportunityRating ?? payload.opportunity_rating,
    opportunityScore:
      payload.opportunityScore ?? payload.opportunity_score,
    budget: budget
      ? {
          minYuan: budget.minYuan ?? budget.min_yuan ?? null,
          maxYuan: budget.maxYuan ?? budget.max_yuan ?? null,
          note: budget.note,
        }
      : null,
    attachments,
  };
}

function formatBudgetAmount(value: number | null | undefined): string {
  return typeof value === "number" ? `¥${value.toLocaleString()}` : "待核实";
}

function GovernmentOpportunityRenderer({
  payload,
}: {
  payload: GovernmentOpportunityPayload;
}) {
  const { t } = useTranslation();
  const {
    summary,
    basicInfo,
    requirementDesc,
    opportunityRating,
    opportunityScore,
    budget,
    attachments,
  } = normalizeGovernmentOpportunityPayload(payload);

  return (
    <div className={styles.resultScrollBody}>
      {/* 基本信息卡片 */}
      {basicInfo ? (
        <Card
          size="small"
          title={t("chat.resultPanel.basicInfo", "基本信息")}
          style={{ marginBottom: 12 }}
        >
          <Descriptions size="small" column={2} bordered>
            <Descriptions.Item label="项目名称">
              {basicInfo.projectName}
            </Descriptions.Item>
            <Descriptions.Item label="客户名称">
              {basicInfo.customerName}
            </Descriptions.Item>
            <Descriptions.Item label="城市">
              {basicInfo.city}
            </Descriptions.Item>
            <Descriptions.Item label="行业">
              {basicInfo.industry}
            </Descriptions.Item>
            <Descriptions.Item label="支撑类型">
              <Tag color="processing">{basicInfo.supportType}</Tag>
            </Descriptions.Item>
          </Descriptions>
          {opportunityRating ? (
            <div style={{ marginTop: 8 }}>
              <Space>
                <Text strong>商机评级：</Text>
                <Tag color={OPPORTUNITY_RATING_COLORS[opportunityRating] || "default"}>
                  {OPPORTUNITY_RATING_LABELS[opportunityRating] || opportunityRating}
                </Tag>
                {opportunityScore != null ? (
                  <Text type="secondary">评分：{opportunityScore}/100</Text>
                ) : null}
              </Space>
            </div>
          ) : null}
          {budget ? (
            <div style={{ marginTop: 4 }}>
              <Text strong>预算区间：</Text>
              <Text type="secondary">
                {formatBudgetAmount(budget.minYuan)} - {formatBudgetAmount(budget.maxYuan)}
                {budget.note ? `（${budget.note}）` : ""}
              </Text>
            </div>
          ) : null}
        </Card>
      ) : null}

      {/* 需求描述 */}
      {requirementDesc ? (
        <Card
          size="small"
          title={t("chat.resultPanel.requirementDesc", "需求描述")}
          style={{ marginBottom: 12 }}
        >
          <Paragraph
            ellipsis={{ rows: 8, expandable: true, symbol: "展开" }}
            style={{ whiteSpace: "pre-wrap" }}
          >
            {requirementDesc}
          </Paragraph>
        </Card>
      ) : null}

      {/* 摘要 */}
      {summary && !requirementDesc ? (
        <Card
          size="small"
          title={t("chat.resultPanel.summary", "分析摘要")}
          style={{ marginBottom: 12 }}
        >
          <Paragraph style={{ whiteSpace: "pre-wrap" }}>
            {summary}
          </Paragraph>
        </Card>
      ) : null}

      {/* 附件 */}
      {attachments.length > 0 ? (
        <Card
          size="small"
          title={t("chat.resultPanel.attachments", "附件")}
        >
          {attachments.map((att, idx) => (
            <div key={idx} style={{ marginBottom: 8 }}>
              <Text>{att.fileName}</Text>
              {att.fileUrl ? (
                <Button
                  type="link"
                  size="small"
                  onClick={() => openExternalLink(att.fileUrl!)}
                >
                  打开
                </Button>
              ) : null}
            </div>
          ))}
        </Card>
      ) : null}
    </div>
  );
}

export function ResultRenderer({ result }: { result: StructuredResultEvent }) {
  const { t } = useTranslation();
  switch (result.result.type) {
    case "business":
      return (
        <BusinessRenderer payload={result.result.payload as StructuredBusinessPayload} />
      );
    case "product":
      return (
        <ProductRenderer payload={result.result.payload as StructuredProductPayload} />
      );
    case "government_opportunity":
      return (
        <GovernmentOpportunityRenderer
          payload={result.result.payload as GovernmentOpportunityPayload}
        />
      );
    case "text":
      return <TextRenderer payload={result.result.payload as StructuredTextPayload} />;
    case "web":
      return <WebRenderer payload={result.result.payload as StructuredWebPayload} />;
    case "pdf":
      return <PdfRenderer payload={result.result.payload as StructuredPdfPayload} />;
    case "html":
      return <HtmlRenderer payload={result.result.payload as StructuredHtmlPayload} />;
    case "table":
      return <TableRenderer payload={result.result.payload as StructuredTablePayload} />;
    case "actions":
      return (
        <ActionsRenderer payload={result.result.payload as StructuredActionsPayload} />
      );
    default:
      return <Empty description={t("chat.resultPanel.unsupported")} />;
  }
}

export interface ResultPanelProps {
  open: boolean;
  result: StructuredResultEvent | null;
  onClose: () => void;
  onRefresh?: () => void;
  onSave?: () => void;
  onViewDetail?: () => void;
  showViewDetail?: boolean;
  updatedAt?: string | null;
  loading?: boolean;
  saveLoading?: boolean;
  isSaved?: boolean;
}

function formatUpdatedAt(value: string | null | undefined): string {
  if (!value) {
    return "";
  }

  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return value;
  }

  return new Date(timestamp).toLocaleString();
}

/**
 * 聊天页右侧结果面板。
 */
export default function ResultPanel({
  open,
  result,
  onClose,
  onRefresh,
  onSave,
  onViewDetail,
  showViewDetail = false,
  updatedAt,
  loading = false,
  saveLoading = false,
  isSaved = false,
}: ResultPanelProps) {
  const { t } = useTranslation();
  const panelTitle = useMemo(
    () => result?.title || t("chat.resultPanel.title"),
    [result, t],
  );

  if (!open) {
    return null;
  }

  return (
    <aside className={styles.resultPanel}>
      <div className={styles.resultPanelHeader}>
        <div className={styles.resultPanelHeaderContent}>
          <Title level={5} style={{ margin: 0 }}>
            {panelTitle}
          </Title>
          {result?.subtitle ? (
            <Text type="secondary">{result.subtitle}</Text>
          ) : null}
          {updatedAt ? (
            <Text type="secondary" className={styles.resultPanelMeta}>
              {t("chat.resultPanel.updatedAt")} {formatUpdatedAt(updatedAt)}
            </Text>
          ) : null}
        </div>
        <Space className={styles.resultPanelHeaderActions}>
          {onRefresh ? (
            <Button type="text" loading={loading} onClick={onRefresh}>
              {t("chat.resultPanel.refresh")}
            </Button>
          ) : null}
          {onSave ? (
            <Button
              type="text"
              loading={saveLoading}
              disabled={isSaved}
              onClick={onSave}
            >
              {isSaved
                ? t("chat.resultPanel.saved")
                : t("chat.resultPanel.save")}
            </Button>
          ) : null}
          {showViewDetail && onViewDetail ? (
            <Button type="text" loading={loading} onClick={onViewDetail}>
              {t("chat.resultPanel.viewDetail")}
            </Button>
          ) : null}
          <Button type="text" onClick={onClose}>
            {t("chat.resultPanel.close")}
          </Button>
        </Space>
      </div>

      <div className={styles.resultPanelBody}>
        {result ? (
          <ResultRenderer result={result} />
        ) : (
          <Empty description={t("chat.resultPanel.empty")} />
        )}
      </div>
    </aside>
  );
}
