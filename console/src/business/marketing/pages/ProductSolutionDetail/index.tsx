import { useEffect, useState } from "react";
import { Button, Card, Empty, Space, Tag, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import {
  marketingResultApi,
  type MarketingResultRecord,
} from "@/api/modules/marketingResult";
import {
  toProductPayloadFromRecord,
} from "@/business/marketing/components/adapters";
import { ProductSolutionDetailContent } from "@/business/marketing/components/detailContent";

const { Paragraph, Title } = Typography;

/**
 * 产品方案详情页，独立展示单条已保存成果，不再联动聊天工作台。
 */
export default function MarketingProductSolutionDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { resultId } = useParams<{ resultId: string }>();
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState<MarketingResultRecord | null>(null);

  useEffect(() => {
    if (!resultId) {
      return;
    }

    setLoading(true);
    void marketingResultApi
      .getResultDetail(Number(resultId))
      .then((response) => {
        setRecord(response);
      })
      .catch((error) => {
        console.error("Failed to load product solution detail:", error);
        setRecord(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [resultId]);

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Button onClick={() => navigate("/biz/marketing/product-solutions")}>
            {t("business.taishan.common.backToList")}
          </Button>
          <Tag color="blue">{t("business.labels.builtinModule")}</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {record?.title || t("business.taishan.productSolutionDetail.title")}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {t("business.taishan.productSolutionDetail.description")}
          </Paragraph>
        </Space>
      </Card>

      <Card loading={loading}>
        {!loading && !record ? (
          <Empty description={t("business.taishan.productSolutionDetail.empty")} />
        ) : null}
        {record ? (
          <ProductSolutionDetailContent
            payload={toProductPayloadFromRecord(record)}
            mode="page"
          />
        ) : null}
      </Card>
    </Space>
  );
}
