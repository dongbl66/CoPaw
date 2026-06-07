# 新业务场景交付包参考

> 优先标准：交付包必须符合 `business-workbench-agent-standard.md`。本文档用于拆分并行开发窗口，所有命名、保存闭环和 Agent/Skill 落点以该标准为准。

## 1. 目标

新业务场景在进入工程实现前，必须先形成一份可并行开发的交付包。交付包用于保证前端、后端、Skill/Agent 三个窗口使用同一套命名、schema、接口和验收口径。

## 2. 交付包目录建议

```text
docs/plans/YYYY-MM-DD-<scene>-implementation-plan.md
docs/plans/YYYY-MM-DD-<scene>-api-contract.md
docs/mockups/<scene>.html
```

如果场景复杂，也可以继续拆分：

```text
docs/plans/YYYY-MM-DD-<scene>-backend-plan.md
docs/plans/YYYY-MM-DD-<scene>-frontend-plan.md
docs/plans/YYYY-MM-DD-<scene>-skill-agent-plan.md
docs/plans/YYYY-MM-DD-<scene>-verification-plan.md
```

## 3. 必须统一的标识

```text
scene id: <scene>
frontend module: <sceneFrontendName>
payload.scene: <scene>_report
meta.bizModule: <scene>
result.type: business
agent id: <scene>_agent
parser import path: backend.scenes.<scene>.parsers.<parser_module>:<parser_func>
hook manifest: backend.scenes.<scene>.manifest
```

这些标识一旦确认，前端、后端、Skill/Agent 三个窗口不得各自改名。

## 4. 三个并行窗口

### 后端窗口

交付范围：

- `src/backend/scenes/<scene>/manifest.py`
- `src/backend/scenes/<scene>/router.py`
- `src/backend/scenes/<scene>/schemas/`
- `src/backend/scenes/<scene>/parsers/`
- `src/backend/scenes/<scene>/hooks/`
- `src/backend/scenes/<scene>/service.py`
- `src/backend/scenes/<scene>/repository.py`
- `src/backend/scenes/<scene>/persistence.py`

边界要求：

- `manifest.py` 注册 router 和 hook factory
- hook factory 必须懒加载
- hook 的 `should_handle` 必须校验 `meta.bizModule` 和 `payload.scene`
- 不为单个新场景修改 `react_agent.py`

### 前端窗口

交付范围：

- `console/src/business/<sceneFrontendName>/manifest.ts`
- `console/src/business/<sceneFrontendName>/pages/`
- `console/src/business/<sceneFrontendName>/workbench/`
- `console/src/api/modules/<sceneFrontendName>Result.ts`
- `console/src/api/types/<sceneFrontendName>.ts`
- `console/src/pages/Chat/result-panel/<Scene>Report.tsx`

边界要求：

- ResultWorkbench 是容器，业务页通过 business manifest 的 `resultWorkbench` 注册
- ResultPanel 优先通过 `payload.scene` 分流
- 默认复用 `result.type = business`
- 页面结构必须包含保存结果列表和详情页，保存成功后通过业务事件刷新列表
- 不另起一套结果展示协议

### Skill/Agent 窗口

交付范围：

- `.qwenpaw/workspaces/<agent_id>/agent.json`
- `.qwenpaw/workspaces/<agent_id>/skill.json`
- `.qwenpaw/workspaces/<agent_id>/PROFILE.md`
- `.qwenpaw/workspaces/<agent_id>/skills/<scene>-question-guide/SKILL.md`
- `.qwenpaw/workspaces/<agent_id>/skills/<scene>-extract-report/SKILL.md`

边界要求：

- 过程辅助型 Skill 只输出自然语言建议
- 报告输出型 Skill 才输出结构化报告
- 报告输出必须进入 `output_binding.final_output_parser_import_path`
- 业务专属 Skill 默认放在工作区 Agent 下，不放到全局 `src/qwenpaw/agents/skills/`

## 5. 统一验收

交付包完成后，至少验证：

- parser 能把模型输出转为 `metadata.structured_result`
- hook 能识别本场景并持久化
- ResultPanel 能展示本场景报告
- ResultWorkbench 能自动展示聊天 JSON
- 保存按钮能在没有 active record 时回查 latest 并保存
- business 页面能加载已保存结果并打开详情
- 两个业务 Skill 职责不混淆
- 端到端 smoke test 能从 Agent 输出走到报告展示
