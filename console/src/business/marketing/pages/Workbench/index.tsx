import { Card, Space, Tag, Typography } from "antd";
import { useTranslation } from "react-i18next";

const { Paragraph, Title, Text } = Typography;

/**
 * 营销业务模块示例工作台。
 */
export default function MarketingWorkbenchPage() {
  const { t } = useTranslation();

  return (
    <Space direction="vertical" size={16} style={{ display: "flex" }}>
      <Card>
        <Space direction="vertical" size={8}>
          <Tag color="orange">{t("business.labels.builtinModule")}</Tag>
          <Title level={3} style={{ margin: 0 }}>
            {t("business.marketing.workbench.title")}
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {t("business.marketing.workbench.description")}
          </Paragraph>
        </Space>
      </Card>

      <Card title={t("business.marketing.workbench.nextStepTitle")}>
        <Space direction="vertical" size={8} style={{ display: "flex" }}>
          <Text>{t("business.marketing.workbench.nextStepOne")}</Text>
          <Text>{t("business.marketing.workbench.nextStepTwo")}</Text>
          <Text>{t("business.marketing.workbench.nextStepThree")}</Text>
        </Space>
      </Card>
    </Space>
  );
}
