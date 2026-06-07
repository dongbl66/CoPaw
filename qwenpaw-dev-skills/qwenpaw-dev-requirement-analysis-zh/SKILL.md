---
name: qwenpaw-dev-requirement-analysis-zh
description: 用于 QwenPaw/CoPaw 项目内新增或改造功能，但开发边界、业务归属、页面接口或 Agent/Skill 链路尚未明确时。
metadata:
  qwenpaw:
    emoji: "📝"
---

# QwenPaw 项目需求分析技能

> 新业务场景需求分析必须先读取 `../references/business-workbench-agent-standard.md`。只要需求包含结构化报告、右侧结果面板、保存、历史列表、详情页、业务 Agent 或业务 Skill，就按完整业务场景评估，而不是按单点功能评估。

## 触发条件

当用户提出要在本项目内新增或改造功能，但尚未形成清晰开发边界时，使用本技能。

## 输入

- 用户提出的业务目标或产品想法
- 已知的项目约束
- 已知的页面、接口、技能或插件线索

## 工作流程

1. 识别需求归属：核心项目、插件 bundle、官网、还是多处联动
2. 明确目标用户与使用场景
3. 梳理页面、交互、接口与数据对象
4. 判断是否需要技能、Agent、插件前端或结构化输出
5. 输出结构化需求说明书

## 输出格式

### 一、需求概述

- 功能名称
- 目标
- 所属范围：核心项目 / 插件 / 官网 / 混合
- 主要入口：Console / Channel / CLI / Plugin UI / Website

### 二、用户场景

| 角色 | 场景 | 目标 |
|------|------|------|
| 开发者 | 在 QwenPaw 中扩展功能 | 快速接入项目现有架构 |
| 最终用户 | 在 Console / Agent / 插件中使用功能 | 正确获得结果 |

### 三、功能范围

- 必做功能
- 可选功能
- 明确不做

### 四、页面与交互

| 页面 / 入口 | 说明 | 是否需要原型 |
|-------------|------|--------------|
| `/console` 页面或插件 UI | 需要展示、编辑、配置或可视化 | 是 |
| CLI / Agent 内部流程 | 纯后端或配置逻辑 | 否 / 视情况 |

### 五、后端与数据

- 需要新增或修改的路由
- 需要新增或修改的配置模型
- 需要新增或修改的 Agent / Skill / Hook / Parser
- 数据读写位置

### 六、结构化输出判断

明确以下问题：

- 是否需要 Pydantic 结构化输出 schema
- 是否需要 `output_binding`
- 是否需要 `final_output_parser`
- 是否需要让 Console 消费 `structured_result`

### 七、验收标准

| 序号 | 验收项 | 条件 |
|------|--------|------|
| 1 | 功能入口可用 | 页面、命令或插件入口正常 |
| 2 | 接口契约稳定 | 请求 / 响应符合合同 |
| 3 | 结构化输出正确 | 若需要，绑定与解析链路完整 |
| 4 | 验证通过 | 至少完成相关 lint / test / build / smoke check |

## 文档落点

建议将需求说明书保存为：

- `docs/plans/YYYY-MM-DD-<topic>-requirements.md`

## 约束

- 不跳过“需求归属”判断
- 不在需求阶段擅自锁死实现细节
- 如果需求涉及结构化输出，必须在需求说明书里明确写出

## 新业务场景需求分析要求

当用户提出一个新的行业、办案、营销、政企、分析、报表或工作台类应用场景时，必须在需求说明书中新增“业务场景归属判断”小节。

详细参考：

- `../references/new-business-scene.md`
- `../references/new-scene-checklist.md`
- `../references/new-scene-delivery-package.md`
- `../references/templates/requirements-template.md`

该小节必须明确：

- 该需求是否属于新业务场景
- 是否需要 Console business 模块
- 是否需要后端 `src/backend/scenes/<scene>/` 场景模块
- 是否需要 Skill / Agent
- 是否需要 `final_output_parser`
- 是否需要 Agent reply hook
- 是否需要结果持久化与历史结果页面
- 是否需要 ResultPanel 展示结构化结果
- 是否复用现有 `StructuredResultEvent`
- 是否需要形成可并行开发的场景交付包

如果需求包含“分析结果、报告输出、结构化面板、历史记录、业务列表、详情页”等能力，默认按新业务场景评估，并优先参考 `marketing`、`fae` 的场景化实现方式。
