# QwenPaw 开发技能集

这套技能用于约束 QwenPaw/CoPaw 项目的新功能、新业务场景、前后端联动、Agent/Skill 和插件开发。目标不是“写一份方案”，而是让每次开发都沉淀为可确认、可并行、可验证的工程交付包。

## 使用入口

优先从主流程技能开始：

```text
qwenpaw-dev-workflow-zh
```

主流程会按阶段调度以下分技能：

| 阶段 | 技能 | 产物 |
| --- | --- | --- |
| 需求分析 | `qwenpaw-dev-requirement-analysis-zh` | 需求说明书 |
| 原型确认 | `qwenpaw-dev-html-prototype-zh` | HTML 原型 |
| API 合同 | `qwenpaw-dev-api-contract-zh` | 接口与结构化结果合同 |
| 后端实现 | `qwenpaw-dev-backend-implementation-zh` | scene/router/parser/hook/persistence |
| 前端实现 | `qwenpaw-dev-frontend-implementation-zh` | business 模块、ResultWorkbench、ResultPanel、保存列表与详情页 |
| Skill/Agent | `qwenpaw-dev-skill-agent-construction-zh` | 工作区 Agent 与业务 Skills |
| 插件集成 | `qwenpaw-dev-plugin-integration-zh` | bundle 接入 |
| 验证 | `qwenpaw-dev-verification-zh` | 验证报告 |

## 新业务场景必须先判定

只要需求包含业务对象、结构化报告、ResultPanel 展示、历史沉淀、Skill/Agent 推理、parser/hook/persistence 任一链路，就按新业务场景处理。

新业务场景不得只新增孤立 Skill、孤立页面或孤立 API。必须优先复用：

```text
business module + backend scene + parser + hook registry + persistence + ResultWorkbench + ResultPanel + saved results list/detail + workspace Agent
```

关键参考：

- `references/business-workbench-agent-standard.md`
- `references/new-business-scene.md`
- `references/new-scene-checklist.md`
- `references/hook-registry.md`
- `references/structured-result-contract.md`
- `references/new-scene-delivery-package.md`
- `examples/fraud-transcript/README.md`

## 并行开发推荐方式

当一个新场景需要多人或多窗口同时实现时，先生成一份“场景交付包”，再拆成三个窗口：

| 窗口 | 范围 | 主要参考 |
| --- | --- | --- |
| 后端窗口 | `src/backend/scenes/<scene>/`、parser、hook、持久化、router | `templates/backend-scene-plan-template.md` |
| 前端窗口 | `console/src/business/<scene>/`、ResultWorkbench 业务页、ResultPanel、保存列表、详情页、API types | `templates/frontend-scene-plan-template.md` |
| Skill/Agent 窗口 | `.qwenpaw/workspaces/<agent_id>/`、两个业务 Skill、output_binding | `templates/skill-agent-plan-template.md` |

每个窗口必须遵守同一组标识：

```text
scene id = <scene>
payload.scene = <scene>_report
meta.bizModule = <scene>
result.type = business
agent id = <scene>_agent
```

## 结构化结果原则

默认复用现有 `StructuredResultEvent`：

```text
eventType = structured_result
result.type = business
payload.scene = <scene>_report
meta.bizModule = <scene>
```

单个业务场景不要为了自身方便新增 `result.type`。只有具备跨场景复用价值时，才扩展 `StructuredResultType`。

## Hook 注册原则

新场景通过 `backend.scenes.<scene>.manifest` 注册 hook factory。不要为了每个场景修改一次 `src/qwenpaw/agents/react_agent.py`。

正确边界：

```text
react_agent.py: 只读取 backend hook registry
backend.scenes.<scene>.manifest: 注册本场景 hook factory
```
