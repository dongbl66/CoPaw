---
name: qwenpaw-dev-html-prototype-zh
description: 用于 QwenPaw/CoPaw 项目内进入工程实现前，需要为 Console、插件前端、官网页面或复杂交互确认 HTML 原型时。
metadata:
  qwenpaw:
    emoji: "🖼️"
---

# QwenPaw 项目 HTML 原型技能

## 触发条件

当需求涉及页面布局、模块入口、列表、表单、状态展示、配置面板或插件 UI 时，使用本技能。

## 输入

- 已确认的需求说明书
- 页面清单与交互说明
- 当前项目的 UI 风格约束

## 工作流程

1. 判断原型归属：Console、插件前端还是官网
2. 选择与现有项目一致的视觉与信息层级
3. 产出单文件 HTML 原型
4. 根据反馈迭代，直到用户确认
5. 为后续 React / 插件 UI 工程化提供组件拆分建议

## 原型落点建议

- Console / 插件 UI 原型：`docs/mockups/<topic>.html`
- 官网展示页原型：`docs/mockups/<topic>-website.html`

## 原型要求

- 使用单文件 HTML，便于直接预览
- 覆盖关键状态：空态、加载态、成功态、错误态
- 展示主要交互：筛选、列表、表单、详情、弹层、状态标签
- 标明建议的组件拆分边界

如果原型对应新业务场景，还必须参考：

- `../references/new-business-scene.md`
- `../references/structured-result-contract.md`
- `../references/new-scene-delivery-package.md`

并在原型或交付说明中标明：

- 是否需要 ResultPanel
- 是否需要 business 列表页和详情页
- ResultPanel 的主要展示区块
- `payload.scene` 的建议值
- 是否建议拆分后端、前端、Skill/Agent 三个并行窗口

## 项目风格约束

### Console / 插件 UI

- 以现有 `console/src/` 风格为主
- 页面头部、卡片、表格、抽屉、弹窗优先参考现有 Console 模式
- 不凭空发明全新导航体系

### 官网

- 以 `website/src/` 的品牌与内容编排为主
- 保持文档站与官网已有排版节奏

## 输出补充

在 HTML 文件末尾或交付说明中补充：

- 推荐的 React 组件拆分
- 推荐的数据结构
- 需要的 API 列表草案

## 确认门

- 原型必须经过用户明确确认
- 若用户提出结构或交互调整，继续迭代原型，不提前进入工程实现
