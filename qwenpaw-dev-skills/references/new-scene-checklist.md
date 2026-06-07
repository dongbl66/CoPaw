# 新业务场景开发检查表

> 使用前先读取 `business-workbench-agent-standard.md`。本检查表必须覆盖 Workbench 自动展示、保存、列表刷新、详情页和 workspace Agent 注册。

## 1. 需求阶段

- [ ] 是否判断该需求属于新业务场景
- [ ] 是否明确目标用户和使用场景
- [ ] 是否明确业务对象
- [ ] 是否明确输入材料
- [ ] 是否明确输出结果
- [ ] 是否明确是否需要历史记录
- [ ] 是否明确是否需要 ResultPanel
- [ ] 是否明确是否需要 Skill / Agent

## 2. 架构阶段

- [ ] 是否选择参考场景：`marketing` / `fae`
- [ ] 是否定义 scene id
- [ ] 是否定义 frontend module name
- [ ] 是否定义 `payload.scene`
- [ ] 是否定义 `meta.bizModule`
- [ ] 是否定义 Agent id
- [ ] 是否明确 result type，优先 `business`

## 3. 后端阶段

- [ ] 是否新增 `src/backend/scenes/<scene>/manifest.py`
- [ ] 是否新增 router
- [ ] 是否新增 schemas
- [ ] 是否新增 parser
- [ ] 是否新增 hook
- [ ] 是否新增 persistence
- [ ] 是否新增 service / repository
- [ ] 是否在 `backend.core.loader` 注册 manifest
- [ ] 是否通过 `backend.core.business_hooks` 注册 hook factory
- [ ] 是否避免重复注册
- [ ] 是否没有为本场景新增 `react_agent.py` 专属分支

## 4. 前端阶段

- [ ] 是否新增 `console/src/business/<scene>/manifest.ts`
- [ ] 是否在 business manifest 中注册 `resultWorkbench`
- [ ] 是否新增 `console/src/business/<scene>/workbench/<Scene>WorkbenchPage.tsx`
- [ ] 是否新增列表页
- [ ] 是否新增详情页
- [ ] 保存结果列表是否只展示已保存结果或明确区分 draft/saved
- [ ] 保存成功后是否派发 `<scene>:results-updated` 并刷新列表
- [ ] 是否新增 API module
- [ ] 是否新增 ResultPanel renderer
- [ ] 是否通过 `payload.scene` 分流
- [ ] 是否复用现有 `StructuredResultEvent`
- [ ] 是否补充 i18n 文案

## 5. Skill / Agent 阶段

- [ ] 是否区分过程辅助型 Skill 和报告输出型 Skill
- [ ] 过程辅助型 Skill 是否禁止输出 `structured_result`
- [ ] 报告输出型 Skill 是否明确 schema
- [ ] 是否新增专用 Agent
- [ ] 业务专属 Skill 是否放在 `.qwenpaw/workspaces/<agent_id>/skills/`
- [ ] 是否绑定 `final_output_parser_import_path`
- [ ] 是否明确 parser import path
- [ ] 是否准备样例输入和样例输出

## 6. 验证阶段

- [ ] parser 单测
- [ ] hook 单测
- [ ] persistence 单测
- [ ] router 单测
- [ ] ResultPanel renderer 测试
- [ ] business 页面测试
- [ ] ResultWorkbench 业务页测试
- [ ] direct JSON 自动显示测试
- [ ] 保存前 latest 回查测试
- [ ] 保存后列表刷新测试
- [ ] Skill 输出检查
- [ ] 端到端 smoke test
