import { useEffect, useMemo, useState } from "react";
import { Button, Card, Empty, Modal, Space, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  marketingResultApi,
  type MarketingOpportunityRecord,
} from "@/api/modules/marketingResult";
import {
  getOpportunityDetailPath,
  toBusinessPayloadFromOpportunity,
} from "@/business/marketing/components/adapters";
import { BusinessDetailContent } from "@/business/marketing/components/detailContent";
import { openExternalLink } from "@/utils/openExternalLink";

const { Paragraph, Title, Text } = Typography;

function formatDateTime(value?: string | null): string {
  if (!value) {
    return "-";
  }
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return value;
  }
  return new Date(timestamp).toLocaleString();
}

/**
 * 泰山石膏市场商机列表页，复用现有商机持久化结果。
 */
export default function MarketingOpportunitiesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<MarketingOpportunityRecord[]>([]);
  const [previewItem, setPreviewItem] = useState<MarketingOpportunityRecord | null>(
    null,
  );

  useEffect(() => {
    setLoading(true);
    void marketingResultApi
      .listOpportunities()
      .then((response) => {
        setItems(response.items);
      })
      .catch((error) => {
        console.error("Failed to load marketing opportunities:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const columns = useMemo<ColumnsType<MarketingOpportunityRecord>>(
    () => [
      {
        title: t("business.taishan.opportunities.columns.title"),
        dataIndex: "title",
        key: "title",
        render: (value: string, record) => (
          <Space direction="vertical" size={2}>
            <Text strong>{value}</Text>
            {record.summary ? (
              <Text type="secondary">{record.summary}</Text>
            ) : null}
          </Space>
        ),
      },
      {
        title: t("business.taishan.opportunities.columns.level"),
        dataIndex: "level",
        key: "level",
        width: 120,
        render: (value?: string | null) =>
          value ? <Tag color="orange">{value}</Tag> : "-",
      },
      {
        title: t("business.taishan.opportunities.columns.region"),
        dataIndex: "region",
        key: "region",
        width: 120,
        render: (value?: string | null) => value || "-",
      },
      {
        title: t("business.taishan.opportunities.columns.budget"),
        dataIndex: "budget",
        key: "budget",
        width: 120,
        render: (value?: number | null) => value ?? "-",
      },
      {
        title: t("business.taishan.opportunities.columns.updatedAt"),
        dataIndex: "updated_at",
        key: "updated_at",
        width: 220,
        render: (value?: string | null) => formatDateTime(value),
      },
      {
        title: t("business.taishan.opportunities.columns.action"),
        key: "action",
        width: 260,
        render: (_, record) => (
          <Space>
            <Button
              type="link"
              onClick={(event) => {
                event.stopPropagation();
                setPreviewItem(record);
              }}
            >
              {t("business.common.preview")}
            </Button>
            <Button
              type="link"
              onClick={(event) => {
                event.stopPropagation();
                navigate(getOpportunityDetailPath(record.id));
              }}
            >
              {t("business.common.viewDetail")}
            </Button>
            {record.original_link ? (
              <Button
                type="link"
                onClick={(event) => {
                  event.stopPropagation();
                  openExternalLink(record.original_link!);
                }}
              >
                {t("business.taishan.opportunities.openSource")}
              </Button>
            ) : null}
          </Space>
        ),
      },
    ],
    [navigate, t],
  );

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Tag color="orange">{t("business.labels.builtinModule")}</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {t("business.taishan.opportunities.title")}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {t("business.taishan.opportunities.description")}
          </Paragraph>
        </Space>
      </Card>

      <Card
        title={t("business.taishan.opportunities.listTitle")}
        extra={
          <Button
            onClick={() => {
              setLoading(true);
              void marketingResultApi
                .listOpportunities()
                .then((response) => {
                  setItems(response.items);
                })
                .catch((error) => {
                  console.error(
                    "Failed to refresh marketing opportunities:",
                    error,
                  );
                })
                .finally(() => {
                  setLoading(false);
                });
            }}
          >
            {t("business.common.refresh")}
          </Button>
        }
      >
        <Table
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={items}
          locale={{
            emptyText: (
              <Empty description={t("business.taishan.opportunities.empty")} />
            ),
          }}
          pagination={false}
        />
      </Card>

      <Modal
        open={!!previewItem}
        title={previewItem?.title || t("business.common.preview")}
        footer={null}
        width={960}
        onCancel={() => setPreviewItem(null)}
      >
        {previewItem ? (
          <BusinessDetailContent
            payload={toBusinessPayloadFromOpportunity(previewItem)}
            mode="embedded"
          />
        ) : null}
      </Modal>
    </Space>
  );
}
