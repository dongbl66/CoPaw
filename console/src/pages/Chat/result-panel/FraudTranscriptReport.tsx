import { Card, Descriptions, Empty, List, Space, Tag, Typography } from "antd";
import { MermaidCodeBlock } from "@/components/MermaidCodeBlock";
import type {
  StructuredBusinessOpportunity,
  StructuredBusinessPayload,
} from "./types";

const { Paragraph, Text } = Typography;

function isMeaningful(value: unknown): boolean {
  return value !== null && value !== undefined && `${value}`.trim().length > 0;
}

function stringifyValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map(stringifyValue).filter(Boolean).join("、");
  }
  if (value && typeof value === "object") {
    return JSON.stringify(value);
  }
  return value === null || value === undefined ? "" : String(value);
}

function metaEntries(data?: Record<string, unknown>) {
  return Object.entries(data ?? {})
    .filter(([, value]) => isMeaningful(value))
    .map(([key, value]) => ({ key, value: stringifyValue(value) }));
}

function resolveMermaid(productInfo?: Record<string, unknown>): string {
  const candidates = [
    "流程图Mermaid",
    "mermaid",
    "Mermaid",
    "flowchartMermaid",
    "pathMermaid",
  ];
  for (const key of candidates) {
    const value = productInfo?.[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function resolveMissingItems(productInfo?: Record<string, unknown>): string[] {
  const value = productInfo?.["缺失项"] ?? productInfo?.missingItems;
  if (Array.isArray(value)) {
    return value.map(stringifyValue).filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) {
    return value
      .split(/[,\n，、]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function BasicInfoSection({ payload }: { payload: StructuredBusinessPayload }) {
  const entries = metaEntries(payload.basicInfo);
  if (!entries.length) {
    return null;
  }
  return (
    <Card size="small" title="基本信息">
      <Descriptions size="small" column={2} bordered>
        {entries.map((entry) => (
          <Descriptions.Item key={entry.key} label={entry.key}>
            {entry.value}
          </Descriptions.Item>
        ))}
      </Descriptions>
    </Card>
  );
}

function FraudPathSection({ payload }: { payload: StructuredBusinessPayload }) {
  const mermaid = resolveMermaid(payload.productInfo);
  const entries = metaEntries(payload.productInfo).filter(
    (entry) =>
      !["流程图Mermaid", "mermaid", "Mermaid", "flowchartMermaid", "pathMermaid"].includes(
        entry.key,
      ),
  );
  return (
    <Card size="small" title="诈骗路径分析">
      <Space direction="vertical" size={12} style={{ display: "flex" }}>
        {payload.productInfo?.["诈骗路径"] ? (
          <Paragraph style={{ marginBottom: 0 }}>
            {stringifyValue(payload.productInfo["诈骗路径"])}
          </Paragraph>
        ) : null}
        {mermaid ? <MermaidCodeBlock chart={mermaid} /> : null}
        {!mermaid && !entries.length && !payload.productInfo?.["诈骗路径"] ? (
          <Empty description="暂无诈骗路径信息" />
        ) : null}
      </Space>
    </Card>
  );
}

function QASection({ opportunities }: { opportunities?: StructuredBusinessOpportunity[] }) {
  if (!opportunities?.length) {
    return (
      <Card size="small" title="问题及答案">
        <Empty description="暂无问答记录" />
      </Card>
    );
  }
  return (
    <Card size="small" title="问题及答案">
      <List
        dataSource={opportunities}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={
                <Space wrap>
                  <Text strong>{item.title}</Text>
                  {item.level ? <Tag color="processing">{item.level}</Tag> : null}
                  {item.type ? <Tag>{item.type}</Tag> : null}
                </Space>
              }
              description={
                <Space direction="vertical" size={4}>
                  {item.summary ? <Text>{item.summary}</Text> : null}
                  {item.reason ? <Text type="secondary">{item.reason}</Text> : null}
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  );
}

function QualitySection({ payload }: { payload: StructuredBusinessPayload }) {
  const productInfo = payload.productInfo ?? {};
  const missingItems = resolveMissingItems(productInfo);
  const qualityEntries = ["质量评分", "风险等级", "建议修正", "qualityScore", "riskLevel", "suggestion"]
    .map((key) => ({ key, value: productInfo[key] }))
    .filter((entry) => isMeaningful(entry.value));

  return (
    <Card size="small" title="质量评估">
      {!qualityEntries.length && !missingItems.length ? (
        <Empty description="暂无质量评估" />
      ) : (
        <Space direction="vertical" size={8} style={{ display: "flex" }}>
          {qualityEntries.map((entry) => (
            <Text key={entry.key}>
              <Text strong>{entry.key}：</Text>
              {stringifyValue(entry.value)}
            </Text>
          ))}
          {missingItems.length ? (
            <Space wrap>
              <Text strong>缺失项：</Text>
              {missingItems.map((item) => (
                <Tag key={item} color="warning">
                  {item}
                </Tag>
              ))}
            </Space>
          ) : null}
        </Space>
      )}
    </Card>
  );
}

export default function FraudTranscriptReport({
  payload,
}: {
  payload: StructuredBusinessPayload;
}) {
  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      {payload.summary ? (
        <Paragraph style={{ marginBottom: 0 }}>{payload.summary}</Paragraph>
      ) : null}
      <BasicInfoSection payload={payload} />
      <FraudPathSection payload={payload} />
      <QASection opportunities={payload.opportunities} />
      <QualitySection payload={payload} />
    </Space>
  );
}

