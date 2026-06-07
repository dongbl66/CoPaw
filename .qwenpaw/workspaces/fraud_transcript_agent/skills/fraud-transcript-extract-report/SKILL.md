---
name: fraud-transcript-extract-report
description: 电诈笔录要素提取与最终报告输出。输入完整或阶段性笔录后，严格输出项目兼容的 StructuredResultEvent JSON，供 ResultPanel 和后端 parser 使用。
---

# 电诈笔录要素提取与报告输出

## 业务定位

用于电诈案件笔录完成后或阶段性总结时，抽取涉诈关键要素，生成诈骗路径分析、问答归纳、质量评估，并输出项目兼容的 `StructuredResultEvent`。

## 输入

- 完整或阶段性电诈笔录文本。
- 可选案件材料，例如聊天记录摘要、转账凭证说明、APP 或平台信息。
- 用户明确要求生成报告、提取要素、形成分析或输出 ResultPanel 报告。

## 输出硬约束

- 只输出一个 JSON 对象。
- 不得输出 Markdown 正文。
- 不得在 JSON 前后添加解释。
- 不得为了生成报告调用 `write_file` 或把 JSON 先写入文件。
- 除非用户明确要求导出文件，否则不要创建 `fraud_transcript_report_output.json` 等中间文件。
- `eventType` 必须是 `structured_result`。
- `version` 必须是 `1.0`。
- `result.type` 必须是 `business`。
- `result.payload.scene` 必须是 `fraud_transcript_report`。
- `meta.bizModule` 必须是 `fraud_transcript`。
- `meta.source` 必须是 `skill`。
- 不得新增不兼容的 `result.type`。
- 不得编造笔录中没有出现的事实；缺失内容写入 `productInfo["缺失项"]`。

## 字段要求

`basicInfo` 至少覆盖：

- `姓名`
- `地址`
- `联系方式`
- `微信号`
- `银行卡号`
- `涉案金额`

`productInfo` 至少覆盖：

- `诈骗路径`
- `流程图Mermaid`
- `质量评分`
- `风险等级`
- `缺失项`
- `建议修正`

`opportunities` 用作问题及答案列表，每条使用：

- `title`: 以 `问题：` 开头。
- `level`: `已回答`、`部分回答` 或 `待补问`。
- `type`: 固定为 `模板问答`。
- `summary`: 笔录中的回答摘要；未回答时写补问目标。
- `reason`: 说明为何已满足或仍需补问。

`attachments` 当前没有附件时输出空数组。

## 执行流程

1. 抽取人员身份、联系方式、账号、银行卡号、涉案金额。
2. 梳理接触、诱导、下载/注册、转账、提现失败、报警处置等诈骗路径。
3. 将路径压缩为 `flowchart LR` Mermaid 字符串。
4. 归纳笔录中的问题及答案，写入 `opportunities`。
5. 根据完整度给出质量评分、风险等级、缺失项和建议修正。
6. 严格按 JSON 模板输出。

## JSON 模板

```json
{
  "eventType": "structured_result",
  "version": "1.0",
  "title": "电诈笔录分析报告",
  "subtitle": "要素提取、诈骗路径与问答分析",
  "result": {
    "type": "business",
    "payload": {
      "title": "电诈笔录分析报告",
      "summary": "",
      "scene": "fraud_transcript_report",
      "basicInfo": {
        "姓名": "",
        "地址": "",
        "联系方式": "",
        "微信号": "",
        "银行卡号": "",
        "涉案金额": ""
      },
      "productInfo": {
        "诈骗路径": "",
        "流程图Mermaid": "flowchart LR\n    A[接触] --> B[诱导]\n    B --> C[转账]",
        "质量评分": 0,
        "风险等级": "",
        "缺失项": [],
        "建议修正": ""
      },
      "opportunities": [
        {
          "title": "问题：你是如何接触到对方的？",
          "level": "已回答",
          "type": "模板问答",
          "summary": "通过微信群接触对方。",
          "reason": "接触渠道已明确。"
        }
      ],
      "attachments": []
    }
  },
  "layout": {
    "autoOpen": true,
    "replace": true,
    "panelWidth": 640
  },
  "meta": {
    "bizModule": "fraud_transcript",
    "source": "skill",
    "timestamp": 0
  }
}
```

## 质量评分

- 90-100：关键事实完整，资金流、账号、平台、证据链清晰。
- 70-89：主线完整，但部分账号、凭证或时间细节缺失。
- 50-69：能看出诈骗过程，但资金流或接触路径不完整。
- 0-49：事实过少，无法形成可靠分析。

## Mermaid 规则

- 使用 `flowchart LR`。
- 节点保持短句，例如“微信群接触”“下载 APP”“首次转账”。
- 不确定环节标记为“待核实”。
- Mermaid 字符串写入 `productInfo["流程图Mermaid"]`。

## 验证点

- 输出可以被 JSON parser 直接解析。
- `payload.scene` 是 `fraud_transcript_report`。
- `meta.bizModule` 是 `fraud_transcript`。
- `basicInfo`、`productInfo`、`opportunities`、`attachments` 都存在。
- 没有 JSON 外的解释文本。
