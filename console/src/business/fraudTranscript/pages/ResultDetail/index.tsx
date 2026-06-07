import { useEffect, useState } from "react";
import { Button, Card, Empty, Space, Tag, Typography } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { fraudTranscriptResultApi } from "@/api/modules/fraudTranscriptResult";
import type { FraudTranscriptResultRecord } from "@/api/types/fraudTranscript";
import FraudTranscriptReport from "@/pages/Chat/result-panel/FraudTranscriptReport";
import type { StructuredBusinessPayload } from "@/pages/Chat/result-panel/types";
import type { StructuredBusinessOpportunity } from "@/pages/Chat/result-panel/types";

const { Paragraph, Title } = Typography;

function toFraudTranscriptPayload(
  record: FraudTranscriptResultRecord,
): StructuredBusinessPayload {
  const structuredResult = record.structured_result as {
    result?: { type?: string; payload?: unknown };
  };
  if (
    structuredResult.result?.type === "business" &&
    structuredResult.result.payload &&
    typeof structuredResult.result.payload === "object"
  ) {
    return structuredResult.result.payload as StructuredBusinessPayload;
  }
  return {
    title: record.title,
    summary: record.summary || undefined,
    scene: record.scene || undefined,
    basicInfo: record.basic_info,
    productInfo: record.product_info,
    opportunities: record.qa_records as unknown as StructuredBusinessOpportunity[],
    attachments: [],
  };
}

export default function FraudTranscriptResultDetailPage() {
  const navigate = useNavigate();
  const { resultId } = useParams<{ resultId: string }>();
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState<FraudTranscriptResultRecord | null>(null);

  useEffect(() => {
    if (!resultId) {
      return;
    }
    setLoading(true);
    void fraudTranscriptResultApi
      .getResult(Number(resultId))
      .then((response) => setRecord(response))
      .catch((error) => {
        console.error("Failed to load fraud transcript result:", error);
        setRecord(null);
      })
      .finally(() => setLoading(false));
  }, [resultId]);

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Button onClick={() => navigate("/biz/fraud-transcript/results")}>
            返回列表
          </Button>
          <Tag color="blue">内置业务模块</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {record?.title || "笔录分析报告详情"}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            展示完整的电诈笔录分析报告，后续可扩展 Word / PDF 导出。
          </Paragraph>
        </Space>
      </Card>
      <Card loading={loading}>
        {!loading && !record ? <Empty description="未找到对应报告" /> : null}
        {record ? <FraudTranscriptReport payload={toFraudTranscriptPayload(record)} /> : null}
      </Card>
    </Space>
  );
}
