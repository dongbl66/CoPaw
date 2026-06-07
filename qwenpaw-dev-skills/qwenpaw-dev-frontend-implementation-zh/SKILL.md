---
name: qwenpaw-dev-frontend-implementation-zh
description: 用于 QwenPaw/CoPaw 项目内 HTML 原型和 API 合同已确认，需要实现 Console、插件前端、官网页面、ResultWorkbench、ResultPanel、保存结果列表或详情页时。
metadata:
  qwenpaw:
    emoji: "⚛️"
---

# QwenPaw 项目前端实现技能

> 新业务场景前端实现必须先读取 `../references/business-workbench-agent-standard.md`，并按 business module + ResultWorkbench 业务页 + 保存结果列表 + 详情页实现。ResultWorkbench 是容器，业务页放在 `console/src/business/<scene>/workbench/`。

## 触发条件

当 API 合同已确认，需要将 HTML 原型转成前端工程代码时，使用本技能。

## 输入

- 已确认的 HTML 原型
- 已确认的 API 合同
- 需求说明书

## 工作流程

1. 判断前端落点：Console、插件前端还是官网
2. 按现有目录模式拆分组件
3. 编写 API 模块与 TypeScript 类型
4. 注册路由或业务模块
5. 补齐测试、国际化、加载态与错误态

## 目录选择规则

### Console 业务模块

优先考虑：

- `console/src/business/<module>/`
- `console/src/api/modules/<module>.ts`
- `console/src/api/types/<module>.ts`
- `console/src/stores/`

如果是现有主页面增强，也可能落到：

- `console/src/pages/...`
- `console/src/components/...`

### 插件前端

优先考虑：

- `plugins/bundle/<plugin_name>/ui/src/`
- 或 `plugins/bundle/<plugin_name>/frontend/src/`

并通过插件 frontend entry 输出到对应 `dist/index.js`

### 官网

优先考虑：

- `website/src/pages/`
- `website/src/components/`
- `website/src/i18n/locales/`

## Console 约束

- 使用 React 18、TypeScript、Vite、Ant Design、i18next、Zustand 的现有组合
- 业务模块优先参考 `console/src/business/marketing/`、`console/src/business/fae/`
- 页面头部、布局、卡片、表格优先复用现有组件
- API 请求复用 `console/src/api/request.ts`
- 文案接入 `console/src/locales/*.json`

## 插件前端约束

- 先查看目标插件是 `ui/` 还是 `frontend/` 结构，再沿用既有模式
- 不在插件里重复实现主项目已有基础设施
- 若需要与宿主通信，优先复用项目现有插件加载与 host external 方式

## 输出要求

- 列出组件拆分
- 说明新增 API 模块与类型定义
- 说明路由 / manifest / 动态模块注册改动
- 明确是否补充前端测试

## 新业务场景前端实现要求

当需求被判定为新业务场景时，Console 前端不得只新增孤立页面。必须优先参考 `console/src/business/marketing/` 与 `console/src/business/fae/` 的 business module 模式。

详细参考：

- `../references/new-business-scene.md`
- `../references/structured-result-contract.md`
- `../references/new-scene-delivery-package.md`
- `../references/templates/frontend-scene-plan-template.md`

必须评估并说明：

- 是否新增 `console/src/business/<scene>/manifest.ts`
- 是否新增业务列表页、详情页或工作台页
- 是否新增 `console/src/api/modules/<scene>Result.ts`
- 是否新增 `console/src/api/types/<scene>.ts`
- 是否需要在 `console/src/business/common/registry/loader.ts` 注册
- 是否复用 Chat ResultPanel
- 是否需要为 `payload.scene` 增加专用 renderer

如果后端输出 `StructuredResultEvent`，前端必须优先复用：

- `console/src/pages/Chat/result-panel/types.ts`
- `console/src/pages/Chat/result-panel/ResultPanel.tsx`
- `console/src/pages/Chat/result-panel/utils.ts`

不要随意新增不兼容的结果协议。若现有 `result.type` 足够承载，优先通过 `payload.scene` 区分业务场景；只有明确需要通用新展示类型时，才扩展 `StructuredResultType`。
