import { useEffect, useMemo, useState } from "react";
import { Button, Card, Empty, Modal, Space, Table, Tag, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  marketingResultApi,
  type MarketingResultRecord,
} from "@/api/modules/marketingResult";
import {
  getProductSolutionDetailPath,
  toProductPayloadFromRecord,
} from "@/business/marketing/components/adapters";
import { ProductSolutionDetailContent } from "@/business/marketing/components/detailContent";

const { Paragraph, Title, Text } = Typography;

function isProductSolutionRecord(item: MarketingResultRecord): boolean {
  const structuredResult = item.info?.structuredResult;
  if (
    structuredResult &&
    typeof structuredResult === "object" &&
    !Array.isArray(structuredResult)
  ) {
    const result = (structuredResult as { result?: unknown }).result;
    if (result && typeof result === "object" && !Array.isArray(result)) {
      const resultType = (result as { type?: unknown }).type;
      if (typeof resultType === "string") {
        return resultType !== "business";
      }
    }
  }

  return item.result_type !== "business";
}

function formatDateTime(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return value;
  }
  return new Date(timestamp).toLocaleString();
}

/**
 * 泰山石膏产品方案列表页，仅展示已手动保存的正式成果。
 */
export default function MarketingProductSolutionsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<MarketingResultRecord[]>([]);
  const [previewItem, setPreviewItem] = useState<MarketingResultRecord | null>(null);

  useEffect(() => {
    setLoading(true);
    void marketingResultApi
      .listSavedResults()
      .then((response) => {
        setItems(response.items.filter(isProductSolutionRecord));
      })
      .catch((error) => {
        console.error("Failed to load saved marketing results:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const columns = useMemo<ColumnsType<MarketingResultRecord>>(
    () => [
      {
        title: t("business.taishan.productSolutions.columns.title"),
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
        title: t("business.taishan.productSolutions.columns.type"),
        dataIndex: "result_type",
        key: "result_type",
        width: 140,
        render: (value: string) => <Tag color="blue">{value}</Tag>,
      },
      {
        title: t("business.taishan.productSolutions.columns.scene"),
        dataIndex: "scene",
        key: "scene",
        width: 160,
        render: (value?: string | null) => value || "-",
      },
      {
        title: t("business.taishan.productSolutions.columns.updatedAt"),
        dataIndex: "updated_at",
        key: "updated_at",
        width: 220,
        render: (value: string) => formatDateTime(value),
      },
      {
        title: t("business.taishan.opportunities.columns.action"),
        key: "action",
        width: 220,
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
                navigate(getProductSolutionDetailPath(record.id));
              }}
            >
              {t("business.common.viewDetail")}
            </Button>
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
          <Tag color="blue">{t("business.labels.builtinModule")}</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {t("business.taishan.productSolutions.title")}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {t("business.taishan.productSolutions.description")}
          </Paragraph>
        </Space>
      </Card>

      <Card
        title={t("business.taishan.productSolutions.savedListTitle")}
        extra={
          <Button
            onClick={() => {
              setLoading(true);
              void marketingResultApi
                .listSavedResults()
                .then((response) => {
                  setItems(response.items.filter(isProductSolutionRecord));
                })
                .catch((error) => {
                  console.error(
                    "Failed to refresh saved marketing results:",
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
              <Empty description={t("business.taishan.productSolutions.empty")} />
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
          <ProductSolutionDetailContent
            payload={toProductPayloadFromRecord(previewItem)}
            mode="embedded"
          />
        ) : null}
      </Modal>
    </Space>
  );
}
