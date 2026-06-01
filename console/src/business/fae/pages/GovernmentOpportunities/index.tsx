import { useMemo, useState } from "react";
import { Button, Input, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import {
  GOVERNMENT_OPPORTUNITY_SUPPORT_TYPES,
  getGovernmentOpportunityListResponse,
  type GovernmentOpportunityListItem,
  type SupportType,
} from "@/business/fae/mock/governmentOpportunities";
import styles from "../governmentOpportunities.module.less";

const { Link, Text } = Typography;

const SUPPORT_TYPE_CLASS_NAME: Record<SupportType, string> = {
  技术支撑: styles.supportTagTechnical,
  方案支撑: styles.supportTagSolution,
  投标支撑: styles.supportTagBidding,
  综合支撑: styles.supportTagComprehensive,
};

interface OverviewStat {
  key: string;
  value: number;
  label: string;
  icon: string;
}

function getGovernmentOpportunityDetailPath(projectId: number): string {
  return `/biz/fae/government-opportunities/${encodeURIComponent(projectId)}`;
}

/**
 * FAE 工作区政企项目商机列表页。
 */
export default function GovernmentOpportunitiesPage() {
  const navigate = useNavigate();
  const [keyword, setKeyword] = useState("");
  const [selectedType, setSelectedType] = useState<"全部类型" | SupportType>(
    "全部类型",
  );
  const response = useMemo(() => getGovernmentOpportunityListResponse(), []);

  const overviewStats = useMemo<OverviewStat[]>(
    () => [
      {
        key: "total",
        value: response.stats.total,
        label: "全部项目",
        icon: "📋",
      },
      {
        key: "active",
        value: response.stats.active,
        label: "活跃商机",
        icon: "✅",
      },
      {
        key: "recent",
        value: response.stats.recent,
        label: "近期更新",
        icon: "⏱️",
      },
      {
        key: "city",
        value: response.stats.cities,
        label: "覆盖城市",
        icon: "🏙️",
      },
    ],
    [response],
  );

  const filteredItems = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return response.list.filter((item) => {
      const matchesType =
        selectedType === "全部类型" || item.supportType === selectedType;
      const matchesKeyword =
        !normalizedKeyword ||
        item.projectName.toLowerCase().includes(normalizedKeyword) ||
        item.customerName.toLowerCase().includes(normalizedKeyword);

      return matchesType && matchesKeyword;
    });
  }, [keyword, selectedType]);

  const columns = useMemo<ColumnsType<GovernmentOpportunityListItem>>(
    () => [
      {
        title: "项目名称",
        dataIndex: "projectName",
        key: "projectName",
        render: (value: string, record) => (
          <Link
            className={styles.projectLink}
            onClick={() => {
              navigate(getGovernmentOpportunityDetailPath(record.id));
            }}
          >
            {value}
          </Link>
        ),
      },
      {
        title: "客户名称",
        dataIndex: "customerName",
        key: "customerName",
      },
      {
        title: "来源（城市）",
        dataIndex: "city",
        key: "city",
        render: (value: string) => (
          <span className={styles.cityCell}>
            <span className={styles.cityDot}>●</span>
            <span>{value}</span>
          </span>
        ),
      },
      {
        title: "创建时间",
        dataIndex: "createTime",
        key: "createTime",
      },
      {
        title: "更新时间",
        dataIndex: "updateTime",
        key: "updateTime",
      },
      {
        title: "行业",
        dataIndex: "industry",
        key: "industry",
      },
      {
        title: "支持类型",
        dataIndex: "supportType",
        key: "supportType",
        render: (value: SupportType) => (
          <span className={`${styles.supportTag} ${SUPPORT_TYPE_CLASS_NAME[value]}`}>
            {value}
          </span>
        ),
      },
    ],
    [navigate],
  );

  return (
    <div className={styles.page}>
      <div className={`${styles.panel} ${styles.header}`}>
        <div className={styles.titleWrap}>
          <span className={styles.titleIcon}>N</span>
          <h2 className={styles.title}>项目商机管理</h2>
        </div>
        <span className={styles.titleCount}>
          共 {response.total} 个项目
        </span>
      </div>

      <div className={styles.statsGrid}>
        {overviewStats.map((item) => (
          <div key={item.key} className={`${styles.panel} ${styles.statCard}`}>
            <div className={styles.statTop}>
              <span className={styles.statIcon}>{item.icon}</span>
              <div>
                <div className={styles.statValue}>{item.value}</div>
                <div className={styles.statLabel}>{item.label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.toolbar}>
        <Input
          allowClear
          size="large"
          value={keyword}
          prefix={<SearchOutlined />}
          className={styles.searchBox}
          placeholder="搜索项目名称、客户名称..."
          onChange={(event) => {
            setKeyword(event.target.value);
          }}
        />

        <div className={styles.filterGroup}>
          {GOVERNMENT_OPPORTUNITY_SUPPORT_TYPES.map((item) => {
            const isActive = item === selectedType;
            return (
              <Button
                key={item}
                className={`${styles.filterButton} ${
                  isActive ? styles.filterButtonActive : ""
                }`}
                onClick={() => {
                  setSelectedType(item);
                }}
              >
                {item}
              </Button>
            );
          })}
        </div>
      </div>

      <div className={`${styles.panel} ${styles.tablePanel}`}>
        <Table<GovernmentOpportunityListItem>
          rowKey="id"
          columns={columns}
          dataSource={filteredItems}
          pagination={false}
          onRow={(record) => ({
            onClick: () => {
              navigate(getGovernmentOpportunityDetailPath(record.id));
            },
          })}
          locale={{
            emptyText: <Text type="secondary">暂无政企项目商机</Text>,
          }}
        />
      </div>
    </div>
  );
}
