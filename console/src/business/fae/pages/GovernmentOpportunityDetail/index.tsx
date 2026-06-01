import { Button, Empty } from "antd";
import { useNavigate, useParams } from "react-router-dom";
import { getGovernmentOpportunityDetailById } from "@/business/fae/mock/governmentOpportunities";
import styles from "../governmentOpportunities.module.less";

function getGovernmentOpportunityListPath(): string {
  return "/biz/fae/government-opportunities";
}

/**
 * FAE 工作区政企项目商机详情页。
 */
export default function GovernmentOpportunityDetailPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const record = getGovernmentOpportunityDetailById(projectId);

  if (!record) {
    return (
      <div className={styles.page}>
        <div className={`${styles.panel} ${styles.detailSection}`}>
          <Empty description="未找到对应项目商机" />
        </div>
      </div>
    );
  }

  const infoCards = [
    { label: "项目名称", value: record.projectName },
    { label: "客户名称", value: record.customerName },
    { label: "来源（城市）", value: record.city },
    { label: "行业", value: record.industry },
    { label: "支持类型", value: record.supportType },
    { label: "创建时间", value: record.createTime },
    { label: "更新时间", value: record.updateTime },
    { label: "项目ID", value: record.id },
  ];

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
                为响应国家“数字政府”建设号召，项目方计划建设统一的业务平台，整合现有分散的政务信息系统，
                实现数据资源的统一管理和共享交换。当前各业务系统独立运行，数据孤岛现象严重，亟需通过统一
                的平台建设提升政务服务效率和市民满意度。
              </div>
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>二、需求概述</div>
              <div className={styles.previewParagraph}>
                本项目核心需求包括：构建 IaaS + PaaS 一体化云底座，支持容器化部署；建立统一数据共享交换平台，
                实现跨部门数据打通；建设统一身份认证和权限管理模块；提供面向市民的移动端政务服务入口；
                满足等保三级安全要求。
              </div>
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>三、技术要求</div>
              <div className={styles.previewParagraph}>
                平台采用微服务架构，支持 Kubernetes 容器编排；数据库需支持分布式部署，具备读写分离能力；
                前端需兼容主流浏览器并适配国产化环境；接口层遵循 RESTful 规范，支持统一 API 网关管理；
                系统需提供 7x24 小时高可用能力，RTO 不超过 30 分钟，RPO 不超过 15 分钟。
              </div>
            </div>

            <div className={styles.previewSection}>
              <div className={styles.previewSectionTitle}>四、实施计划</div>
              <div className={styles.previewParagraph}>
                项目分三期建设：一期完成基础云平台搭建和核心数据打通；二期完成业务系统迁移；三期完成智能化
                应用上线和整体优化。每期需提供详细里程碑计划和验收标准。
              </div>
            </div>

            <div className={styles.previewFooter}>本文档为项目需求预览说明，仅供内部参考使用 | 项目 1 / 1</div>
          </div>
        </div>
      </div>
    </div>
  );
}
