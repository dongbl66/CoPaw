import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Empty, Space, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useNavigate } from "react-router-dom";
import { fraudTranscriptResultApi } from "@/api/modules/fraudTranscriptResult";
import type { FraudTranscriptResultRecord } from "@/api/types/fraudTranscript";

const { Paragraph, Text, Title } = Typography;

function formatDateTime(value: string): string {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? value : new Date(timestamp).toLocaleString();
}

export default function FraudTranscriptResultsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [savedOnly, setSavedOnly] = useState(false);
  const [items, setItems] = useState<FraudTranscriptResultRecord[]>([]);

  const loadResults = useCallback(() => {
    setLoading(true);
    void fraudTranscriptResultApi
      .listResults(savedOnly)
      .then((response) => setItems(response.items))
      .catch((error) => {
        console.error("Failed to load fraud transcript results:", error);
      })
      .finally(() => setLoading(false));
  }, [savedOnly]);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  useEffect(() => {
    const handleResultsUpdated = () => {
      loadResults();
    };
    window.addEventListener(
      "fraud-transcript:results-updated",
      handleResultsUpdated,
    );
    return () => {
      window.removeEventListener(
        "fraud-transcript:results-updated",
        handleResultsUpdated,
      );
    };
  }, [loadResults]);

  const columns = useMemo<ColumnsType<FraudTranscriptResultRecord>>(
    () => [
      {
        title: "报告标题",
        dataIndex: "title",
        key: "title",
        render: (value: string, record) => (
          <Space direction="vertical" size={2}>
            <Text strong>{value}</Text>
            {record.summary ? <Text type="secondary">{record.summary}</Text> : null}
          </Space>
        ),
      },
      {
        title: "保存状态",
        dataIndex: "save_status",
        key: "save_status",
        width: 120,
        render: (value: string) => (
          <Tag color={value === "saved" ? "green" : "default"}>{value}</Tag>
        ),
      },
      {
        title: "会话",
        dataIndex: "session_id",
        key: "session_id",
        width: 180,
        render: (value?: string | null) => value || "-",
      },
      {
        title: "更新时间",
        dataIndex: "updated_at",
        key: "updated_at",
        width: 220,
        render: (value: string) => formatDateTime(value),
      },
      {
        title: "操作",
        key: "action",
        width: 180,
        render: (_, record) => (
          <Space>
            <Button
              type="link"
              onClick={() => navigate(`/biz/fraud-transcript/results/${record.id}`)}
            >
              查看详情
            </Button>
            {record.save_status !== "saved" ? (
              <Button
                type="link"
                onClick={() => {
                  setLoading(true);
                  void fraudTranscriptResultApi
                    .saveResult(record.id)
                    .then(() => {
                      window.dispatchEvent(
                        new CustomEvent("fraud-transcript:results-updated"),
                      );
                    })
                    .finally(() => setLoading(false));
                }}
              >
                标记保存
              </Button>
            ) : null}
          </Space>
        ),
      },
    ],
    [navigate, savedOnly],
  );

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Tag color="blue">内置业务模块</Tag>
          <Title level={3} style={{ margin: 0 }}>
            电诈笔录
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            查看笔录分析报告、诈骗路径、问答归纳和质量评估结果。
          </Paragraph>
        </Space>
      </Card>
      <Card
        title="历史报告"
        extra={
          <Space>
            <Button onClick={() => setSavedOnly((value) => !value)}>
              {savedOnly ? "显示全部" : "仅看已保存"}
            </Button>
            <Button
              onClick={() => {
                loadResults();
              }}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={items}
          locale={{ emptyText: <Empty description="暂无笔录分析报告" /> }}
          pagination={false}
        />
      </Card>
    </Space>
  );
}
