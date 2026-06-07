# 新业务场景 Workbench + Agent 标准

本标准用于新增或改造 QwenPaw/CoPaw 业务场景。凡是需求包含结构化报告、右侧结果面板、保存、历史列表、详情页、业务 Agent 或业务 Skill，应默认按本标准设计。

## 标准交付链路

```text
需求分析
-> API 合同
-> 后端 scene
-> structured_result parser
-> BusinessPostReplyHook
-> persistence / repository / service / router
-> Console business module
-> ResultWorkbench 业务页
-> 保存结果列表 / 详情页
-> workspace Agent
-> Agent 内业务 Skills
-> .qwenpaw/config.json 注册
-> 验证
```

不要只实现其中一段。例如“接口返回 200”不等于完成；还必须验证聊天 JSON 是否自动打开右侧 Workbench、点击保存是否进入业务列表、列表是否能打开详情。

## 命名必须统一

在进入实现前先确定并固定以下值：

```text
scene id: <scene>
frontend module: <sceneFrontendName>
payload.scene: <scene>_report
meta.bizModule: <scene>
result.type: business
agent id: <scene>_agent
workspace: .qwenpaw/workspaces/<agent_id>/
backend scene: src/backend/scenes/<scene>/
frontend module path: console/src/business/<sceneFrontendName>/
```

这些值一旦确认，需求、API、后端、前端、Skill/Agent、验证文档必须使用同一套命名。不要出现 `scene=fae`、`payload.scene=fraud_transcript_report`、`meta.bizModule=marketing` 这类混用。

## 后端标准

后端业务场景默认包含：

```text
src/backend/scenes/<scene>/
  manifest.py
  router.py
  service.py
  repository.py
  persistence.py
  schemas/
  parsers/
  hooks/
```

要求：

- `manifest.py` 注册 router 和 hook factory。
- hook 的 `should_handle` 必须校验 `meta.bizModule` 与 `payload.scene`。
- parser 必须把 Agent 输出转换为可解析的 `structured_result`。
- persistence 必须保存结构化结果，以支持 latest、save、list、detail。
- 不要为了单个业务场景修改 `react_agent.py`；新场景通过 hook registry / scene manifest 接入。

## 前端标准

前端业务场景默认包含：

```text
console/src/business/<sceneFrontendName>/
  manifest.ts
  pages/
    Results/
    ResultDetail/
  workbench/
    <Scene>WorkbenchPage.tsx

console/src/api/modules/<sceneFrontendName>Result.ts
console/src/api/types/<sceneFrontendName>.ts
```

要求：

- `manifest.ts` 必须注册 routes、menus；需要右侧结果面板时还要注册 `resultWorkbench`。
- `ResultWorkbench` 是容器，业务渲染逻辑放在 `console/src/business/<sceneFrontendName>/workbench/`。
- 业务 Workbench 必须支持 direct JSON 立即显示。
- 点击保存时，如果只有 direct JSON、没有 active record，必须先按 `session_id + biz_module` 拉取 latest，再保存。
- 保存成功后派发业务事件，例如 `<scene>:results-updated`，让列表页刷新。
- 保存结果列表页默认调用 `listResults(true)` 或等价 saved-only API。
- 详情页必须从保存记录还原 `structured_result` 并渲染完整报告。

## Skill / Agent 标准

业务专属 Agent 默认创建在：

```text
.qwenpaw/workspaces/<agent_id>/
  agent.json
  skill.json
  PROFILE.md
  skills/<scene>-question-guide/SKILL.md
  skills/<scene>-extract-report/SKILL.md
```

要求：

- 先按业务逻辑拆技能，再创建 workspace Agent。
- 过程辅助类 Skill 只给补问、检查、引导建议。
- 报告输出类 Skill 才输出 `structured_result` JSON。
- 报告输出 Skill 必须要求“没有 JSON 外解释文本”。
- `skill.json` 登记该 Agent 自己的 skills。
- `agent.json.id`、目录名、`.qwenpaw/config.json` profile key 必须一致。
- `.qwenpaw/config.json` 只追加 agent，不删除或覆盖已有 agent；不要修改 `active_agent`，除非用户明确要求。
- 业务专属 Skill 不要放到全局 `src/qwenpaw/agents/skills/`。

## 结构化结果标准

业务报告输出推荐：

```json
{
  "eventType": "structured_result",
  "version": "1.0",
  "title": "<report title>",
  "result": {
    "type": "business",
    "payload": {
      "scene": "<scene>_report",
      "basicInfo": {},
      "productInfo": {},
      "opportunities": [],
      "attachments": []
    }
  },
  "meta": {
    "bizModule": "<scene>",
    "source": "skill"
  }
}
```

如果场景确实不是 `business` 类型，必须在 API 合同中说明为何不能复用 `business`，并同步说明前端 ResultWorkbench 如何分流。

## 验证清单

至少验证：

- Agent 输出 JSON 可以被 `JSON.parse` 解析。
- `payload.scene` 与 `meta.bizModule` 正确。
- 后端 latest API 支持 `session_id + biz_module`。
- 聊天 JSON 出现后，右侧 Workbench 自动显示。
- 点击刷新只拉取当前业务的 latest，不串到 marketing / fae / fraud 等其他业务。
- 点击保存可以在没有 active record 时回查 latest 并保存。
- 保存成功后业务列表刷新。
- 保存列表可打开详情页。
- 详情页展示结构化报告。
- frontend tests、TypeScript、build 通过。

## 参考实现

- `fraud_transcript`：完整业务 Agent、双 Skill、结构化报告、后端 scene、ResultWorkbench、保存列表、详情页。
- `fae`：ResultWorkbench 容器化、FAE 保存结果列表、详情页、保存刷新事件。
