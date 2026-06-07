# 电诈笔录智能辅助示例

## 1. 场景定义

```text
scene id: fraud_transcript
frontend module: fraudTranscript
payload.scene: fraud_transcript_report
meta.bizModule: fraud_transcript
agent id: fraud_transcript_agent
```

## 2. Skill

```text
fraud-transcript-question-guide
- 类型：过程辅助型
- 输出：自然语言提问建议
- 不输出 structured_result

fraud-transcript-extract-report
- 类型：报告输出型
- 输出：StructuredResultEvent
- 触发 ResultWorkbench，并由 ResultPanel 渲染报告
```

## 3. 后端

```text
src/backend/scenes/fraud_transcript/
  manifest.py
  router.py
  service.py
  repository.py
  persistence.py
  parsers/transcript_report.py
  hooks/post_reply.py
```

## 4. 前端

```text
console/src/business/fraudTranscript/
  manifest.ts
  pages/Results/
  pages/ResultDetail/
  workbench/FraudTranscriptWorkbenchPage.tsx
console/src/pages/Chat/result-panel/FraudTranscriptReport.tsx
console/src/api/modules/fraudTranscriptResult.ts
```

## 5. 结构化结果

```text
eventType = structured_result
result.type = business
payload.scene = fraud_transcript_report
meta.bizModule = fraud_transcript
```

## 6. 验收

- 模板提问 Skill 可用
- 报告输出 Skill 可用
- Parser 注入 metadata
- Hook 保存报告
- ResultWorkbench 自动显示聊天 JSON
- 保存按钮可回查 latest 并保存
- ResultPanel 展示报告
- 保存后历史报告列表刷新
- 历史报告详情可打开

## 7. 并行开发窗口

后端窗口：

```text
src/backend/scenes/fraud_transcript/
```

必须实现 manifest、parser、hook、persistence、router，并通过 `backend.scenes.fraud_transcript.manifest` 注册 hook factory。

前端窗口：

```text
console/src/business/fraudTranscript/
  manifest.ts
  workbench/FraudTranscriptWorkbenchPage.tsx
  pages/Results/
  pages/ResultDetail/
console/src/pages/Chat/result-panel/FraudTranscriptReport.tsx
```

必须通过 business manifest 注册 `resultWorkbench`。ResultWorkbench 作为容器加载 `FraudTranscriptWorkbenchPage`；业务页负责 latest、direct JSON 显示、保存、详情跳转；ResultPanel 只负责按 `payload.scene = fraud_transcript_report` 渲染报告。

Skill/Agent 窗口：

```text
.qwenpaw/workspaces/fraud_transcript_agent/
  agent.json
  skill.json
  skills/fraud-transcript-question-guide/SKILL.md
  skills/fraud-transcript-extract-report/SKILL.md
```

第一个 Skill 只做模板提问和追问建议，不输出结构化结果；第二个 Skill 负责要素提取和报告输出，并进入 parser/hook/persistence/ResultWorkbench/ResultPanel/保存列表链路。
