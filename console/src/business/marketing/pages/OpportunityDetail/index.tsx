import { useEffect, useState } from "react";
import { Button, Card, Empty, Space, Tag, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import {
  marketingResultApi,
  type MarketingOpportunityRecord,
} from "@/api/modules/marketingResult";
import {
  toBusinessPayloadFromOpportunity,
} from "@/business/marketing/components/adapters";
import { BusinessDetailContent } from "@/business/marketing/components/detailContent";

const { Paragraph, Title } = Typography;

/**
 * 市场商机详情页，直接展示单条商机详情。
 */
export default function MarketingOpportunityDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { opportunityId } = useParams<{ opportunityId: string }>();
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState<MarketingOpportunityRecord | null>(null);

  useEffect(() => {
    if (!opportunityId) {
      return;
    }

    setLoading(true);
    void marketingResultApi
      .getOpportunityDetail(Number(opportunityId))
      .then((response) => {
        setRecord(response);
      })
      .catch((error) => {
        console.error("Failed to load marketing opportunity detail:", error);
        setRecord(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [opportunityId]);

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Button onClick={() => navigate("/biz/marketing/opportunities")}>
            {t("business.taishan.common.backToList")}
          </Button>
          <Tag color="orange">{t("business.labels.builtinModule")}</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {record?.title || t("business.taishan.opportunityDetail.title")}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {t("business.taishan.opportunityDetail.description")}
          </Paragraph>
        </Space>
      </Card>

      <Card loading={loading}>
        {!loading && !record ? (
          <Empty description={t("business.taishan.opportunityDetail.empty")} />
        ) : null}
        {record ? (
          <BusinessDetailContent
            payload={toBusinessPayloadFromOpportunity(record)}
            mode="page"
          />
        ) : null}
      </Card>
    </Space>
  );
}
