---
name: qwenpaw-dev-workflow-zh
description: 用于在 QwenPaw/CoPaw 项目内开发新功能、新业务场景、新页面、新接口、新技能、新 workspace Agent、ResultWorkbench 或新插件。
metadata:
  qwenpaw:
    emoji: "🧭"
---

# QwenPaw 项目开发主流程技能

> 新业务场景必须先读取 `../references/business-workbench-agent-standard.md`，并按“backend scene + Console business module + ResultWorkbench 业务页 + 保存结果列表/详情页 + workspace Agent + Agent 内业务 Skills + .qwenpaw/config.json 注册”的完整链路设计，不要只实现孤立 API、孤立页面或孤立 Skill。

本技能是这套开发技能的总入口。它不直接实现具体代码，而是负责判断需求归属、安排阶段顺序、控制确认门，并在合适的阶段调用对应分技能。

## 项目定位

在 QwenPaw/CoPaw 仓库中，新增需求通常属于以下四类之一：

1. 核心后端能力：`src/qwenpaw/`
2. Console 前端能力：`console/src/`
3. 官网或文档站能力：`website/src/`
4. 插件 / bundle 能力：`plugins/bundle/<plugin_name>/`

在进入实现前，先判断本次需求主要落在哪一类；如果跨多类，记录主落点和联动点。

## 强制主流程

### 0. 项目结构识别

先识别本次需求会接入哪些目录：

- 核心后端 API / Agent / 配置：`src/qwenpaw/app/`、`src/qwenpaw/agents/`、`src/qwenpaw/config/`
- Console 前端：`console/src/api/`、`console/src/pages/`、`console/src/business/`、`console/src/plugins/`
- 官网：`website/src/`
- 插件 bundle：`plugins/bundle/<plugin_name>/`
- 测试：`tests/`、`console/src/**/*.test.tsx`
- 原型 / 设计文档：`docs/mockups/`、`docs/plans/`

### 1. 需求说明书

Use Skill: `qwenpaw-dev-requirement-analysis-zh`

输出需求说明书，至少包含：

- 功能目标与用户场景
- 改动范围：核心项目 / 插件 / 双方联动
- 页面与交互清单
- 数据对象与接口需求
- 是否需要技能、Agent 或结构化输出
- 验收标准

建议把需求说明书存放到：

- `docs/plans/YYYY-MM-DD-<topic>-requirements.md`

确认门：
需求说明书未确认，不进入 HTML 原型或工程实现。

### 2. HTML 原型

Use Skill: `qwenpaw-dev-html-prototype-zh`

当需求涉及 Console 页面、插件前端界面、官网页面或复杂交互时，先产出单文件 HTML 原型，用于多轮确认。

建议原型输出到：

- `docs/mockups/<topic>.html`

确认门：
HTML 原型必须经过多轮确认。原型未确认，不进入 API 合同和工程实现。

### 3. API 合同

Use Skill: `qwenpaw-dev-api-contract-zh`

HTML 原型确认后，再设计接口合同与数据边界。合同中必须明确：

- 路由落点：核心 `src/qwenpaw/app/routers/` 或插件 `plugins/bundle/<plugin_name>/router.py` / `routers/`
- 请求 / 响应 DTO
- 是否需要结构化输出绑定
- 前端调用映射

建议 API 合同输出到：

- `docs/plans/YYYY-MM-DD-<topic>-api-contract.md`

确认门：
API 合同未确认，不进入并行实现阶段。

### 4. 并行实现阶段

API 合同确认后，以下任务可以并行推进：

- 前端工程实现：Use Skill `qwenpaw-dev-frontend-implementation-zh`
- 后端工程实现：Use Skill `qwenpaw-dev-backend-implementation-zh`
- 技能 / Agent 构建：Use Skill `qwenpaw-dev-skill-agent-construction-zh`
- 插件集成：Use Skill `qwenpaw-dev-plugin-integration-zh`

并行阶段的关键原则：

- 所有实现都以已确认的 API 合同为准
- 路由层、Agent 层、结构化输出解析层职责分开
- 插件优先复用项目已有注册与挂载模式
- 不做需求外扩展

### 5. 汇总验证

Use Skill: `qwenpaw-dev-verification-zh`

当并行任务完成后，统一执行：

- 前端 lint / test / build
- Python 测试或目标模块测试
- 必要的启动验证
- 技能 / Agent / 插件目录完整性检查

## 分技能清单

| 阶段 | 技能 |
|------|------|
| 需求分析 | `qwenpaw-dev-requirement-analysis-zh` |
| HTML 原型 | `qwenpaw-dev-html-prototype-zh` |
| API 合同 | `qwenpaw-dev-api-contract-zh` |
| 前端实现 | `qwenpaw-dev-frontend-implementation-zh` |
| 后端实现 | `qwenpaw-dev-backend-implementation-zh` |
| 技能与 Agent | `qwenpaw-dev-skill-agent-construction-zh` |
| 插件集成 | `qwenpaw-dev-plugin-integration-zh` |
| 验证 | `qwenpaw-dev-verification-zh` |

## 输出要求

- 每个阶段开始前先调用对应分技能
- 每个确认门都等待用户明确确认
- 文档优先沉淀到 `docs/plans/` 或 `docs/mockups/`
- 最终输出应包含：变更文件、关键命令、验证结果、未验证风险

## 新业务场景开发强制要求

当需求属于新的业务应用场景，而不是单点工具、普通页面或通用配置能力时，必须按项目现有业务场景链路进行设计，不能只给孤立 Skill、孤立页面或孤立 API。

详细规则优先参考：

- `../references/new-business-scene.md`
- `../references/new-scene-checklist.md`
- `../references/new-scene-delivery-package.md`
- `../examples/fraud-transcript/README.md`

方案必须先判断是否涉及以下链路：

- Console business 模块：`console/src/business/<scene>/manifest.ts`
- 后端业务场景模块：`src/backend/scenes/<scene>/`
- 结构化输出 parser：`src/backend/scenes/<scene>/parsers/`
- Agent reply hook：`src/backend/scenes/<scene>/hooks/`
- 结果持久化：`repository.py`、`service.py`、`persistence.py`
- 业务 API：`router.py`
- ResultPanel 渲染：`console/src/pages/Chat/result-panel/`
- 技能 / Agent：`.qwenpaw/workspaces/<agent_id>/skills/`、`AgentProfileConfig.output_binding`

方案输出时必须显式回答：

- 是否是新业务场景
- 参考哪个已有场景，优先参考 `marketing` 或 `fae`
- 是否需要 `business manifest`
- 是否需要 `final_output_parser`
- 是否需要 `BusinessPostReplyHook`
- 是否需要持久化结果和历史结果页面
- ResultPanel 是否复用现有 `StructuredResultEvent`
- 是否需要拆成后端、前端、Skill/Agent 三个并行开发窗口

如果新业务场景需要结构化报告输出，必须优先复用现有 `structured_result` / `ResultPanel` / hook / persistence 链路，不能另起一套不兼容的 schema 或展示协议。

进入实现前，应优先按 `../references/new-scene-delivery-package.md` 输出一份场景交付包，统一 scene id、`payload.scene`、`meta.bizModule`、Agent id、parser import path 和 hook manifest。
