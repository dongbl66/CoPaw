---
name: fae-government-opportunity-extract-report
description: 政企/FAE 商机报告要求提取与结构化结果输出。用户提供调研材料、招投标信息、客户需求、项目线索或要求生成商机分析报告、报告要求提取、ResultPanel 结果时，必须使用本技能，输出可被 FAE 后端 parser 和右侧结果面板消费的 StructuredResultEvent JSON。
---

# FAE 商机报告要求提取与结果输出

## 业务定位

用于 `ra-agentv1` 在完成政企客户调研、招投标材料分析、客户需求挖掘或项目商机研判后，提取“报告要求”和商机核心字段，并输出项目兼容的 `StructuredResultEvent`。

这个 JSON 会被后端 FAE post-reply hook 自动解析并持久化到：

- FAE 右侧 ResultPanel 最新结果
- FAE 政企商机列表
- FAE 商机详情页

## 触发场景

当用户出现以下意图时使用本技能：

- “生成 FAE 报告”
- “提取报告要求”
- “分析这个政企项目/客户需求/招投标信息”
- “形成商机分析”
- “输出到右侧结果面板”
- “保存到 FAE 商机列表”
- 用户提供客户材料、项目背景、招标公告、需求说明、调研纪要，并要求结构化分析

## 输入

- 客户名称、项目名称、城市、行业等基本信息
- 调研纪要、招投标公告、需求文档、聊天材料、会议纪要
- 客户痛点、预算、时间要求、技术诉求、交付边界
- 可选附件信息，例如 PDF、网页、文档路径

## 输出硬约束

- 只输出一个 JSON 对象。
- 不得输出 Markdown 正文。
- 不得在 JSON 前后添加解释文本。
- 不得把 JSON 只写在 reasoning；JSON 必须出现在最终 message 中。
- 不得为了生成结果调用 `write_file` 或先写入中间文件。
- 除非用户明确要求导出文件，否则不要创建报告文件。
- `eventType` 必须是 `structured_result`。
- `version` 必须是 `1.0`。
- `result.type` 必须是 `government_opportunity`。
- `result.payload.scene` 必须是 `government_opportunity`。
- `meta.bizModule` 必须是 `fae`。
- `meta.source` 必须是 `skill`。
- 不确定的信息写“待核实”或留空字符串，不得编造事实。

## 字段要求

`basicInfo` 至少覆盖：

- `projectName`: 项目名称
- `customerName`: 客户名称
- `city`: 城市
- `industry`: 行业
- `supportType`: 支撑类型，只能是 `技术支撑`、`方案支撑`、`投标支撑`、`综合支撑`

`payload` 顶层还必须包含：

- `title`: 报告标题
- `summary`: 一句话商机摘要
- `requirementDesc`: 报告要求和客户需求描述，尽量分点写清楚
- `opportunityRating`: 只能是 `high`、`medium`、`low`
- `opportunityScore`: 0-100 整数
- `budget`: 预算区间对象
- `opportunities`: 商机判断、待补充问题、跟进建议列表
- `attachments`: 附件列表，没有附件时输出空数组

## 支撑类型判断

- `技术支撑`: 主要是技术方案、架构、接口、部署、安全、性能、产品适配等技术问题。
- `方案支撑`: 主要是售前方案、需求梳理、建设路径、价值论证、汇报材料。
- `投标支撑`: 明确涉及招标、投标、标书、评分项、资质、控标、响应文件。
- `综合支撑`: 同时涉及技术、方案、投标或交付等多个方面。

## 商机评分

- 90-100: 客户、项目、预算、需求、时间、决策链清晰，近期可推进。
- 70-89: 主线完整，但预算、决策人、时间或竞争信息部分缺失。
- 50-69: 有明确需求，但客户意向、预算或项目边界不完整。
- 0-49: 信息过少，仅能形成初步线索。

`opportunityRating` 映射规则：

- `high`: 80-100
- `medium`: 50-79
- `low`: 0-49

## 执行流程

1. 提取项目名称、客户名称、城市、行业、支撑类型。
2. 提取报告要求：客户想解决什么问题、需要什么材料、希望呈现什么结论。
3. 梳理需求描述：业务背景、现状痛点、建设目标、技术/方案/投标要求。
4. 判断预算区间；没有预算时 `minYuan` 和 `maxYuan` 写 `null`，并在 `note` 说明“材料未体现预算”。
5. 评估商机等级和分数，并说明关键依据。
6. 归纳待补充问题和下一步跟进动作，写入 `opportunities`。
7. 严格按 JSON 模板输出。

## JSON 模板

```json
{
  "eventType": "structured_result",
  "version": "1.0",
  "title": "FAE 政企商机分析报告",
  "subtitle": "报告要求提取、客户需求与商机研判",
  "result": {
    "type": "government_opportunity",
    "payload": {
      "scene": "government_opportunity",
      "title": "FAE 政企商机分析报告",
      "summary": "",
      "basicInfo": {
        "projectName": "",
        "customerName": "",
        "city": "",
        "industry": "",
        "supportType": "方案支撑"
      },
      "requirementDesc": "",
      "opportunityRating": "medium",
      "opportunityScore": 60,
      "budget": {
        "minYuan": null,
        "maxYuan": null,
        "note": "材料未体现预算"
      },
      "opportunities": [
        {
          "title": "商机判断：客户需求是否明确",
          "level": "部分明确",
          "type": "报告要求提取",
          "summary": "",
          "reason": ""
        },
        {
          "title": "待补充：预算与决策链",
          "level": "待核实",
          "type": "跟进问题",
          "summary": "补充预算范围、决策部门、采购方式、项目时间表。",
          "reason": "这些信息影响商机等级和推进优先级。"
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
    "bizModule": "fae",
    "source": "skill",
    "timestamp": 0
  }
}
```

## 验证点

- 输出可以被 JSON parser 直接解析。
- `result.type` 是 `government_opportunity`。
- `payload.scene` 是 `government_opportunity`。
- `meta.bizModule` 是 `fae`。
- `basicInfo.projectName`、`basicInfo.customerName`、`basicInfo.supportType` 存在。
- `requirementDesc` 存在，且包含报告要求/客户需求。
- `opportunities` 和 `attachments` 都存在。
- 没有 JSON 外的解释文本。
