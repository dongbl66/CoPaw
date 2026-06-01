import { Button, Card, Descriptions, Empty, Space, Typography } from "antd";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type {
  StructuredBusinessPayload,
  StructuredProductPayload,
  StructuredWorkbenchAttachment,
} from "@/pages/Chat/result-panel/types";
import { openExternalLink } from "@/utils/openExternalLink";

const { Paragraph, Text } = Typography;

type DetailMode = "panel" | "page" | "embedded";

function renderMetaEntries(
  data: Record<string, unknown> | undefined,
): Array<{ key: string; value: string }> {
  if (!data) {
    return [];
  }

  return Object.entries(data)
    .filter(([, value]) => value !== null && value !== undefined && `${value}`.trim())
    .map(([key, value]) => ({
      key,
      value: typeof value === "string" ? value : JSON.stringify(value),
    }));
}

function AttachmentPreviewSection({
  attachments,
}: {
  attachments?: StructuredWorkbenchAttachment[];
}) {
  const { t } = useTranslation();

  if (!attachments?.length) {
    return null;
  }

  return (
    <Space direction="vertical" size={12} style={{ display: "flex" }}>
      <Text strong>{t("chat.resultPanel.attachments")}</Text>
      {attachments.map((attachment, index) => {
        const primaryLink =
          attachment.previewUrl ||
          attachment.downloadUrl ||
          attachment.fileUrl ||
          attachment.filePath;

        return (
          <Card
            key={`${attachment.fileName || "attachment"}-${index}`}
            size="small"
          >
            <Space
              direction="vertical"
              size={8}
              style={{ display: "flex", width: "100%" }}
            >
              <Space style={{ justifyContent: "space-between", width: "100%" }}>
                <Text strong>
                  {attachment.fileName || t("chat.resultPanel.unnamedAttachment")}
                </Text>
                <Text type="secondary">{attachment.kind}</Text>
              </Space>
              {primaryLink ? (
                <Button
                  type="link"
                  style={{ paddingInline: 0 }}
                  onClick={() => {
                    openExternalLink(primaryLink);
                  }}
                >
                  {t("chat.resultPanel.openAttachment")}
                </Button>
              ) : null}
            </Space>
          </Card>
        );
      })}
    </Space>
  );
}

export function BusinessDetailContent({
  payload,
  mode = "panel",
  footerActions,
}: {
  payload: StructuredBusinessPayload;
  mode?: DetailMode;
  footerActions?: React.ReactNode;
}) {
  const { t } = useTranslation();
  const metaEntries = useMemo(
    () => renderMetaEntries(payload.basicInfo),
    [payload.basicInfo],
  );

  const cardSize = mode === "page" ? "default" : "small";

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      {payload.summary ? (
        <Paragraph style={{ marginBottom: 0 }}>{payload.summary}</Paragraph>
      ) : null}

      {!!metaEntries.length && (
        <Card size={cardSize} title={t("chat.resultPanel.basicInfo")}>
          <Descriptions size="small" column={2} bordered>
            {metaEntries.map((entry) => (
              <Descriptions.Item key={entry.key} label={entry.key}>
                {entry.value}
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )}

      {!!payload.opportunities?.length && (
        <Space direction="vertical" size={12} style={{ display: "flex" }}>
          <Text strong>{t("chat.resultPanel.opportunities")}</Text>
          {payload.opportunities.map((item, index) => (
            <Card
              key={`${item.title}-${index}`}
              size={cardSize}
              title={item.title}
              extra={item.level ? <Text type="secondary">{item.level}</Text> : null}
            >
              <Space direction="vertical" size={8} style={{ display: "flex" }}>
                <Space size={[8, 8]} wrap>
                  {item.region ? <Text>{item.region}</Text> : null}
                  {item.source ? <Text>{item.source}</Text> : null}
                  {item.budget !== undefined ? (
                    <Text>{`${t("chat.resultPanel.budget")}: ${item.budget}`}</Text>
                  ) : null}
                </Space>
                {item.summary ? <Text type="secondary">{item.summary}</Text> : null}
                {item.reason ? (
                  <Paragraph style={{ marginBottom: 0 }}>{item.reason}</Paragraph>
                ) : null}
                {item.originalLink ? (
                  <Button
                    type="link"
                    style={{ paddingInline: 0 }}
                    onClick={() => {
                      openExternalLink(item.originalLink!);
                    }}
                  >
                    {t("chat.resultPanel.openSource")}
                  </Button>
                ) : null}
              </Space>
            </Card>
          ))}
        </Space>
      )}

      <AttachmentPreviewSection attachments={payload.attachments} />

      {footerActions ? <div>{footerActions}</div> : null}
    </Space>
  );
}

export function ProductSolutionDetailContent({
  payload,
  mode = "panel",
  footerActions,
}: {
  payload: StructuredProductPayload;
  mode?: DetailMode;
  footerActions?: React.ReactNode;
}) {
  const { t } = useTranslation();
  const metaEntries = useMemo(
    () => renderMetaEntries(payload.productInfo),
    [payload.productInfo],
  );
  const cardSize = mode === "page" ? "default" : "small";

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      {payload.summary ? (
        <Paragraph style={{ marginBottom: 0 }}>{payload.summary}</Paragraph>
      ) : null}

      {payload.richText ? (
        <Card size={cardSize} title={t("chat.resultPanel.solutionContent")}>
          <Paragraph style={{ marginBottom: 0 }}>{payload.richText}</Paragraph>
        </Card>
      ) : null}

      {!!metaEntries.length && (
        <Card size={cardSize} title={t("chat.resultPanel.productInfo")}>
          <Descriptions size="small" column={2} bordered>
            {metaEntries.map((entry) => (
              <Descriptions.Item key={entry.key} label={entry.key}>
                {entry.value}
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )}

      <AttachmentPreviewSection attachments={payload.attachments} />

      {footerActions ? <div>{footerActions}</div> : null}
    </Space>
  );
}

export function EmptyDetailContent() {
  const { t } = useTranslation();
  return <Empty description={t("chat.resultPanel.empty")} />;
}
