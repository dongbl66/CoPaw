import { useEffect, useMemo, useState } from "react";
import { Button, Empty, Spin } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import DisplayContentPreview from "@/business/common/components/DisplayContentPreview";
import type { DisplayContentItem } from "@/business/common/components/DisplayContentPreview";
import { faeResultApi } from "@/api/modules/faeResult";
import type { FAEOpportunityDetailResponse } from "@/api/modules/faeResult";
import styles from "../governmentOpportunities.module.less";

interface GovernmentOpportunityDetailView {
  id: number;
  projectName: string;
  customerName: string;
  city: string;
  createTime: string;
  updateTime: string;
  industry: string;
  supportType: string;
  requirementDesc: string;
  displayContent: DisplayContentItem[];
}

function getGovernmentOpportunityListPath(): string {
  return "/biz/fae/government-opportunities";
}

function toDetailView(
  record: FAEOpportunityDetailResponse,
): GovernmentOpportunityDetailView {
  return {
    id: record.id,
    projectName: record.project_name,
    customerName: record.customer_name,
    city: record.city,
    createTime: record.create_time,
    updateTime: record.update_time,
    industry: record.industry,
    supportType: record.support_type,
    requirementDesc: record.requirement_desc,
    displayContent: record.display_content as DisplayContentItem[],
  };
}

export default function GovernmentOpportunityDetailPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const [loading, setLoading] = useState(false);
  const [record, setRecord] = useState<GovernmentOpportunityDetailView | null>(
    null,
  );

  useEffect(() => {
    if (!projectId) {
      setRecord(null);
      return;
    }

    setLoading(true);
    void faeResultApi
      .getOpportunity(projectId)
      .then((response) => {
        setRecord(toDetailView(response));
      })
      .catch((error) => {
        console.error("Failed to load FAE opportunity detail:", error);
        setRecord(null);
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  const infoCards = useMemo(
    () =>
      record
        ? [
            { label: "项目名称", value: record.projectName },
            { label: "客户名称", value: record.customerName },
            { label: "来源（城市）", value: record.city },
            { label: "行业", value: record.industry },
            { label: "支持类型", value: record.supportType },
            { label: "创建时间", value: record.createTime },
            { label: "更新时间", value: record.updateTime },
            { label: "项目ID", value: record.id },
          ]
        : [],
    [record],
  );

  if (loading && !record) {
    return (
      <div className={styles.page}>
        <div className={`${styles.panel} ${styles.detailSection}`}>
          <Spin />
        </div>
      </div>
    );
  }

  if (!record) {
    return (
      <div className={styles.page}>
        <div className={`${styles.panel} ${styles.detailSection}`}>
          <Empty description="未找到对应项目商机" />
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={`${styles.panel} ${styles.detailSection}`}>
        <div className={styles.breadcrumbRow}>
          <Button
            onClick={() => {
              navigate(getGovernmentOpportunityListPath());
            }}
          >
            返回项目列表
          </Button>
          <span>项目商机管理 / 项目详情</span>
        </div>
      </div>

      <div className={`${styles.panel} ${styles.detailSection}`}>
        <div className={styles.sectionTitle}>项目基本信息</div>
        <div className={styles.infoGrid}>
          {infoCards.map((item) => (
            <div key={item.label} className={styles.infoCard}>
              <div className={styles.infoLabel}>{item.label}</div>
              <div className={styles.infoValue}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className={`${styles.panel} ${styles.detailSection}`}>
        <div className={styles.sectionTitle}>需求描述</div>
        <div className={styles.descriptionBox}>{record.requirementDesc}</div>
      </div>

      <div className={`${styles.panel} ${styles.detailSection}`}>
        <div className={styles.sectionTitle}>需求报告预览</div>
        <DisplayContentPreview
          items={record.displayContent}
          emptyText="暂无需求报告文件"
        />
      </div>
    </div>
  );
}
