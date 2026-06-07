import type React from "react";
import type { ResultBizModule } from "@/api/modules/unifiedResult";
import type { StructuredResultEvent } from "@/pages/Chat/result-panel/types";

/**
 * 业务页面路由声明。
 */
export interface BusinessRouteDeclaration {
  key: string;
  path: string;
  label: string;
  component: React.ComponentType;
  activeMenuKey?: string;
  priority?: number;
  icon?: string;
}

/**
 * 业务菜单声明。
 */
export interface BusinessMenuDeclaration {
  key: string;
  path: string;
  label: string;
  groupKey: string;
  priority?: number;
  icon?: string;
}

/**
 * 右侧结果工作台页面声明。
 */
export interface ResultWorkbenchPageProps {
  sessionId: string | null;
  open: boolean;
  refreshSignal: number;
  directResult: StructuredResultEvent | null;
  pendingToolResult?: unknown;
  onOpenChange: (open: boolean) => void;
}

export interface BusinessResultWorkbenchManifest {
  bizModule: ResultBizModule;
  Page: React.ComponentType<ResultWorkbenchPageProps>;
}

/**
 * 前端业务模块 Manifest。
 */
export interface BusinessModuleManifest {
  id: string;
  name: string;
  version: string;
  enabledByDefault?: boolean;
  routes: BusinessRouteDeclaration[];
  menus: BusinessMenuDeclaration[];
  resultWorkbench?:
    | BusinessResultWorkbenchManifest
    | BusinessResultWorkbenchManifest[];
}
