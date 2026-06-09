import { Button, Empty, Space, Table, Typography, Tag, Descriptions, Card } from "antd";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  BusinessDetailContent,
  ProductSolutionDetailContent,
} from "@/business/marketing/components/detailContent";
import { DisplayContentPreview } from "@/business/common/components/DisplayContentPreview";
import { adaptStructuredResult } from "@/business/common/registry/structuredResultAdapters";
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
  StructuredViewModelPayload,
  StructuredWebPayload,
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

function ViewModelRenderer({ payload }: { payload: StructuredViewModelPayload }) {
  const { t } = useTranslation();

  return (
    <div className={styles.resultScrollBody}>
      {payload.summary ? (
        <Card
          size="small"
          title={t("chat.resultPanel.summary", "分析摘要")}
          style={{ marginBottom: 12 }}
        >
          <Paragraph style={{ whiteSpace: "pre-wrap" }}>
            {payload.summary}
          </Paragraph>
        </Card>
      ) : null}

      {payload.sections.map((section) => (
        <Card
          key={section.key}
          size="small"
          title={section.title}
          style={{ marginBottom: 12 }}
        >
          {section.fields && section.fields.length > 0 ? (
            <Descriptions size="small" column={2} bordered>
              {section.fields.map((field) => (
                <Descriptions.Item
                  key={field.key ?? field.label}
                  label={field.label}
                >
                  {field.variant === "tag" ? (
                    <Tag color={field.color || "default"}>{field.value}</Tag>
                  ) : (
                    field.value ?? ""
                  )}
                </Descriptions.Item>
              ))}
            </Descriptions>
          ) : null}

          {section.text ? (
            <Paragraph
              ellipsis={{ rows: 8, expandable: true, symbol: "展开" }}
              style={{ whiteSpace: "pre-wrap" }}
            >
              {section.text}
            </Paragraph>
          ) : null}

          {section.attachments && section.attachments.length > 0 ? (
            <DisplayContentPreview items={section.attachments} />
          ) : null}
        </Card>
      ))}
    </div>
  );
}

export function ResultRenderer({ result }: { result: StructuredResultEvent }) {
  const { t } = useTranslation();
  const adaptedResult = adaptStructuredResult(result);
  if (adaptedResult !== result) {
    return <ResultRenderer result={adaptedResult} />;
  }

  switch (result.result.type) {
    case "business":
      return (
        <BusinessRenderer payload={result.result.payload as StructuredBusinessPayload} />
      );
    case "product":
      return (
        <ProductRenderer payload={result.result.payload as StructuredProductPayload} />
      );
    case "view_model":
      return (
        <ViewModelRenderer
          payload={result.result.payload as StructuredViewModelPayload}
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
