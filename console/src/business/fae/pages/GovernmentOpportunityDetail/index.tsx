import { useEffect, useMemo, useState } from "react";
import { Button, Empty, Spin } from "antd";
import { useNavigate, useParams } from "react-router-dom";
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
        <div className={styles.sectionTitle}>需求文档（PDF预览）</div>
        <div className={styles.previewShell}>
          <div className={styles.previewDocument}>
            <div className={styles.previewTopLine} />
            <h3 className={styles.previewTitle}>
              {record.projectName}需求规格说明书
            </h3>
            <div className={styles.previewMeta}>
              版本：V1.0 | 日期：{record.updateTime} | 项目编号：{record.id}
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>一、项目背景</div>
              <div className={styles.previewParagraph}>
                为响应数字化建设要求，项目方计划建设统一业务平台，整合现有分散的信息系统，实现数据资源的统一管理和共享交换。
              </div>
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>二、需求概述</div>
              <div className={styles.previewParagraph}>{record.requirementDesc}</div>
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>三、技术要求</div>
              <div className={styles.previewParagraph}>
                平台需满足高可用、可扩展、统一认证、权限管理、接口规范和安全合规要求。
              </div>
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>四、实施计划</div>
              <div className={styles.previewParagraph}>
                建议分阶段推进：先完成基础能力建设，再完成业务迁移和智能化应用上线。
              </div>
            </div>

            <div className={styles.previewFooter}>
              本文档为项目需求预览说明，仅供内部参考使用 | 项目 {record.id} / 1
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
