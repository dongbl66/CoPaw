import type React from "react";

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
 * 前端业务模块 Manifest。
 */
export interface BusinessModuleManifest {
  id: string;
  name: string;
  version: string;
  enabledByDefault?: boolean;
  routes: BusinessRouteDeclaration[];
  menus: BusinessMenuDeclaration[];
}
