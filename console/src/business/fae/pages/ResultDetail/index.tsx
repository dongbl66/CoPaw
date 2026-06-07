import { useEffect, useState } from "react";
import { Button, Card, Empty, Space, Tag, Typography } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { faeResultApi } from "@/api/modules/faeResult";
import type { FAEResultRecord } from "@/api/modules/faeResult";
import { ResultRenderer } from "@/pages/Chat/result-panel/ResultPanel";
import type { StructuredResultEvent } from "@/pages/Chat/result-panel/types";
import { toStructuredResultEventFromFAERecord } from "@/pages/Chat/result-panel/utils";

const { Paragraph, Title } = Typography;

export default function FaeResultDetailPage() {
  const navigate = useNavigate();
  const { resultId } = useParams<{ resultId: string }>();
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState<FAEResultRecord | null>(null);
  const [structuredResult, setStructuredResult] =
    useState<StructuredResultEvent | null>(null);

  useEffect(() => {
    if (!resultId) {
      return;
    }

    setLoading(true);
    void faeResultApi
      .getResultDetail(resultId)
      .then((response) => {
        setRecord(response);
        setStructuredResult(toStructuredResultEventFromFAERecord(response));
      })
      .catch((error) => {
        console.error("Failed to load FAE result:", error);
        setRecord(null);
        setStructuredResult(null);
      })
      .finally(() => setLoading(false));
  }, [resultId]);

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Button onClick={() => navigate("/biz/fae/results")}>
            Back to Results
          </Button>
          <Tag color="blue">FAE</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {record?.title || "FAE Result Detail"}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            View the saved FAE opportunity report generated from chat.
          </Paragraph>
        </Space>
      </Card>
      <Card loading={loading}>
        {!loading && !structuredResult ? (
          <Empty description="FAE result not found" />
        ) : null}
        {structuredResult ? <ResultRenderer result={structuredResult} /> : null}
      </Card>
    </Space>
  );
}
