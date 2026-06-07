import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Empty, Space, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useNavigate } from "react-router-dom";
import { faeResultApi } from "@/api/modules/faeResult";
import type { FAEResultRecord } from "@/api/modules/faeResult";

const { Paragraph, Text, Title } = Typography;

function formatDateTime(value: string): string {
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? value : new Date(timestamp).toLocaleString();
}

export default function FaeResultsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<FAEResultRecord[]>([]);

  const loadResults = useCallback(() => {
    setLoading(true);
    void faeResultApi
      .listResults(true)
      .then((response) => setItems(response.items))
      .catch((error) => {
        console.error("Failed to load FAE results:", error);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  useEffect(() => {
    window.addEventListener("fae:results-updated", loadResults);
    return () => {
      window.removeEventListener("fae:results-updated", loadResults);
    };
  }, [loadResults]);

  const columns = useMemo<ColumnsType<FAEResultRecord>>(
    () => [
      {
        title: "Title",
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
        title: "Status",
        dataIndex: "save_status",
        key: "save_status",
        width: 120,
        render: (value?: string) => (
          <Tag color={value === "saved" ? "green" : "default"}>
            {value || "draft"}
          </Tag>
        ),
      },
      {
        title: "Session",
        dataIndex: "session_id",
        key: "session_id",
        width: 180,
        render: (value?: string | null) => value || "-",
      },
      {
        title: "Updated At",
        dataIndex: "updated_at",
        key: "updated_at",
        width: 220,
        render: (value: string) => formatDateTime(value),
      },
      {
        title: "Actions",
        key: "action",
        width: 140,
        render: (_, record) => (
          <Button
            type="link"
            onClick={() => navigate(`/biz/fae/results/${record.id}`)}
          >
            View Detail
          </Button>
        ),
      },
    ],
    [navigate],
  );

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Tag color="blue">FAE</Tag>
          <Title level={3} style={{ margin: 0 }}>
            FAE Saved Results
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            Review saved FAE opportunity reports generated from chat.
          </Paragraph>
        </Space>
      </Card>
      <Card
        title="Saved Results"
        extra={<Button onClick={loadResults}>Refresh</Button>}
      >
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={items}
          locale={{ emptyText: <Empty description="No saved FAE results" /> }}
          pagination={false}
        />
      </Card>
    </Space>
  );
}
