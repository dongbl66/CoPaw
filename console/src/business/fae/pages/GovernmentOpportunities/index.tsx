import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Empty, Input, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { faeResultApi } from "@/api/modules/faeResult";
import type { FAEOpportunityRecord } from "@/api/modules/faeResult";
import styles from "../governmentOpportunities.module.less";

const { Link } = Typography;

const ALL_SUPPORT_TYPES = "全部类型";
const GOVERNMENT_OPPORTUNITY_SUPPORT_TYPES = [
  ALL_SUPPORT_TYPES,
  "技术支撑",
  "方案支撑",
  "投标支撑",
  "综合支撑",
] as const;

type SupportFilter = (typeof GOVERNMENT_OPPORTUNITY_SUPPORT_TYPES)[number];

const SUPPORT_TYPE_CLASS_NAME: Record<string, string> = {
  技术支撑: styles.supportTagTechnical,
  方案支撑: styles.supportTagSolution,
  投标支撑: styles.supportTagBidding,
  综合支撑: styles.supportTagComprehensive,
};

interface GovernmentOpportunityListItem {
  id: number;
  projectName: string;
  customerName: string;
  city: string;
  createTime: string;
  updateTime: string;
  industry: string;
  supportType: string;
}

interface OverviewStat {
  key: string;
  value: number;
  label: string;
  icon: string;
}

function getGovernmentOpportunityDetailPath(projectId: number): string {
  return `/biz/fae/government-opportunities/${encodeURIComponent(projectId)}`;
}

function toListItem(record: FAEOpportunityRecord): GovernmentOpportunityListItem {
  return {
    id: record.id,
    projectName: record.project_name,
    customerName: record.customer_name,
    city: record.city,
    createTime: record.create_time,
    updateTime: record.update_time,
    industry: record.industry,
    supportType: record.support_type,
  };
}

export default function GovernmentOpportunitiesPage() {
  const navigate = useNavigate();
  const [keyword, setKeyword] = useState("");
  const [selectedType, setSelectedType] =
    useState<SupportFilter>(ALL_SUPPORT_TYPES);
  const [items, setItems] = useState<GovernmentOpportunityListItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadOpportunities = useCallback(() => {
    setLoading(true);
    void faeResultApi
      .listOpportunities()
      .then((response) => {
        setItems(response.items.map(toListItem));
      })
      .catch((error) => {
        console.error("Failed to load FAE opportunities:", error);
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadOpportunities();
  }, [loadOpportunities]);

  useEffect(() => {
    window.addEventListener("fae:results-updated", loadOpportunities);
    return () => {
      window.removeEventListener("fae:results-updated", loadOpportunities);
    };
  }, [loadOpportunities]);

  const overviewStats = useMemo<OverviewStat[]>(() => {
    const cities = new Set(items.map((item) => item.city).filter(Boolean));
    return [
      {
        key: "total",
        value: items.length,
        label: "全部项目",
        icon: "N",
      },
      {
        key: "active",
        value: items.length,
        label: "活跃商机",
        icon: "A",
      },
      {
        key: "recent",
        value: items.length,
        label: "近期更新",
        icon: "R",
      },
      {
        key: "city",
        value: cities.size,
        label: "覆盖城市",
        icon: "C",
      },
    ];
  }, [items]);

  const filteredItems = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return items.filter((item) => {
      const matchesType =
        selectedType === ALL_SUPPORT_TYPES || item.supportType === selectedType;
      const matchesKeyword =
        !normalizedKeyword ||
        item.projectName.toLowerCase().includes(normalizedKeyword) ||
        item.customerName.toLowerCase().includes(normalizedKeyword);

      return matchesType && matchesKeyword;
    });
  }, [items, keyword, selectedType]);

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
        render: (value: string) => (
          <span
            className={`${styles.supportTag} ${
              SUPPORT_TYPE_CLASS_NAME[value] ?? ""
            }`}
          >
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
        <span className={styles.titleCount}>共 {items.length} 个项目</span>
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
          loading={loading}
          columns={columns}
          dataSource={filteredItems}
          pagination={false}
          onRow={(record) => ({
            onClick: () => {
              navigate(getGovernmentOpportunityDetailPath(record.id));
            },
          })}
          locale={{
            emptyText: <Empty description="暂无政企项目商机" />,
          }}
        />
      </div>
    </div>
  );
}
