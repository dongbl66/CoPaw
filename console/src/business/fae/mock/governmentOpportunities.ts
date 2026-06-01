export type SupportType =
  | "技术支撑"
  | "方案支撑"
  | "投标支撑"
  | "综合支撑";

/**
 * 政企项目商机列表项。
 */
export interface GovernmentOpportunityListItem {
  id: number;
  projectName: string;
  customerName: string;
  city: string;
  createTime: string;
  updateTime: string;
  industry: string;
  supportType: SupportType;
}

/**
 * 政企项目商机列表返回。
 */
export interface GovernmentOpportunityListResponse {
  list: GovernmentOpportunityListItem[];
  total: number;
  page: number;
  pageSize: number;
  stats: {
    total: number;
    active: number;
    recent: number;
    cities: number;
  };
}

/**
 * 政企项目商机详情返回。
 */
export interface GovernmentOpportunityDetailResponse
  extends GovernmentOpportunityListItem {
  requirementDesc: string;
  pdfurl: string;
}

export const GOVERNMENT_OPPORTUNITY_SUPPORT_TYPES: Array<
  "全部类型" | SupportType
> = ["全部类型", "技术支撑", "方案支撑", "投标支撑", "综合支撑"];

const GOVERNMENT_OPPORTUNITY_LIST: GovernmentOpportunityListItem[] = [
  {
    id: 1,
    projectName: "智慧政务云平台建设项目",
    customerName: "广州市政务服务数据管理局",
    city: "广州",
    createTime: "2025-11-15",
    updateTime: "2026-05-20",
    industry: "政府",
    supportType: "技术支撑",
  },
  {
    id: 2,
    projectName: "商业银行核心系统升级改造",
    customerName: "深圳前海微众银行",
    city: "深圳",
    createTime: "2026-01-08",
    updateTime: "2026-05-18",
    industry: "金融",
    supportType: "方案支撑",
  },
  {
    id: 3,
    projectName: "智能制造MES系统实施",
    customerName: "东莞华为精密制造有限公司",
    city: "东莞",
    createTime: "2026-02-20",
    updateTime: "2026-05-15",
    industry: "制造业",
    supportType: "投标支撑",
  },
  {
    id: 4,
    projectName: "智慧校园综合管理平台",
    customerName: "佛山市南海区教育局",
    city: "佛山",
    createTime: "2025-12-10",
    updateTime: "2026-04-28",
    industry: "教育",
    supportType: "综合支撑",
  },
  {
    id: 5,
    projectName: "智慧医疗影像云平台",
    customerName: "惠州市中心人民医院",
    city: "惠州",
    createTime: "2026-03-05",
    updateTime: "2026-05-22",
    industry: "医疗",
    supportType: "技术支撑",
  },
  {
    id: 6,
    projectName: "新能源汽车充电桩运营平台",
    customerName: "广州小鹏汽车科技有限公司",
    city: "广州",
    createTime: "2026-01-22",
    updateTime: "2026-05-10",
    industry: "制造业",
    supportType: "方案支撑",
  },
  {
    id: 7,
    projectName: "全域旅游大数据分析平台",
    customerName: "珠海市文化广电旅游体育局",
    city: "珠海",
    createTime: "2025-10-18",
    updateTime: "2026-05-08",
    industry: "政府",
    supportType: "投标支撑",
  },
  {
    id: 8,
    projectName: "跨境电商供应链协同平台",
    customerName: "深圳市跨境电子商务协会",
    city: "深圳",
    createTime: "2026-04-02",
    updateTime: "2026-05-25",
    industry: "互联网",
    supportType: "综合支撑",
  },
];

const GOVERNMENT_OPPORTUNITY_DETAIL_MAP: Record<
  number,
  GovernmentOpportunityDetailResponse
> = {
  1: {
    ...GOVERNMENT_OPPORTUNITY_LIST[0],
    requirementDesc: "本项目需要构建一个统一的政务云平台...",
    pdfurl: "",
  },
  2: {
    ...GOVERNMENT_OPPORTUNITY_LIST[1],
    requirementDesc: "围绕核心系统升级、容灾切换与交易性能提升提供专项方案支撑。",
    pdfurl: "",
  },
  3: {
    ...GOVERNMENT_OPPORTUNITY_LIST[2],
    requirementDesc: "以制造执行、设备联动与质量追溯为核心，输出实施规划。",
    pdfurl: "",
  },
  4: {
    ...GOVERNMENT_OPPORTUNITY_LIST[3],
    requirementDesc: "输出校园治理、数据中台、移动门户与综合运维方案。",
    pdfurl: "",
  },
  5: {
    ...GOVERNMENT_OPPORTUNITY_LIST[4],
    requirementDesc: "围绕影像归档、跨院区共享与容灾存储提供技术支撑。",
    pdfurl: "",
  },
  6: {
    ...GOVERNMENT_OPPORTUNITY_LIST[5],
    requirementDesc: "聚焦充电网络调度、运营分析与会员服务，补齐方案架构。",
    pdfurl: "",
  },
  7: {
    ...GOVERNMENT_OPPORTUNITY_LIST[6],
    requirementDesc: "整理项目背景、数据治理策略与投标技术应答内容。",
    pdfurl: "",
  },
  8: {
    ...GOVERNMENT_OPPORTUNITY_LIST[7],
    requirementDesc: "围绕订单协同、供应商管理与物流链路可视化输出综合支撑方案。",
    pdfurl: "",
  },
};

export const GOVERNMENT_OPPORTUNITY_LIST_RESPONSE: GovernmentOpportunityListResponse =
  {
    list: GOVERNMENT_OPPORTUNITY_LIST,
    total: GOVERNMENT_OPPORTUNITY_LIST.length,
    page: 1,
    pageSize: 20,
    stats: {
      total: GOVERNMENT_OPPORTUNITY_LIST.length,
      active: GOVERNMENT_OPPORTUNITY_LIST.length,
      recent: 5,
      cities: new Set(GOVERNMENT_OPPORTUNITY_LIST.map((item) => item.city)).size,
    },
  };

/**
 * 获取静态项目列表响应。
 */
export function getGovernmentOpportunityListResponse(): GovernmentOpportunityListResponse {
  return GOVERNMENT_OPPORTUNITY_LIST_RESPONSE;
}

/**
 * 根据项目 ID 查询单条商机详情。
 */
export function getGovernmentOpportunityDetailById(
  projectId?: string,
): GovernmentOpportunityDetailResponse | null {
  const numericId = Number(projectId);
  if (!Number.isFinite(numericId)) {
    return null;
  }

  return GOVERNMENT_OPPORTUNITY_DETAIL_MAP[numericId] ?? null;
}
