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

`payload` 顶层只保留以下字段，且字段名必须严格一致：

- `output`
- `project_name`
- `customer_name`
- `city`
- `industry`
- `support_type`
- `requirement_desc`
- `opportunity_rating`
- `opportunity_score`
- `budget`
- `display_content`

其中：

- `output` 是一句话摘要
- `support_type` 只能是 `技术支撑`、`方案支撑`、`投标支撑`、`综合支撑`
- `opportunity_rating` 只能是 `high`、`medium`、`low`
- `budget.min_yuan` 和 `budget.max_yuan` 用数字；没有预算时写 `null`
- `display_content` 是附件列表，没有附件时输出空数组

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
4. 判断预算区间；没有预算时 `min_yuan` 和 `max_yuan` 写 `null`，并在 `note` 说明“材料未体现预算”。
5. 评估商机等级和分数，并写入 `output` 一句话摘要。
6. 严格按 JSON 模板输出，不要额外添加 `opportunities`、`attachments` 之外的业务字段。

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
      "output": "识别到高价值商机：客户名称 + 项目简述，预算约 X-XX 万",
      "project_name": "项目全称",
      "customer_name": "客户全称",
      "city": "城市名",
      "industry": "所属行业",
      "support_type": "技术支撑 或 方案支撑 或 投标支撑 或 综合支撑",
      "requirement_desc": "需求描述全文，分点列出核心诉求",
      "opportunity_rating": "high 或 medium 或 low",
      "opportunity_score": 85,
      "budget": {
        "min_yuan": 28000,
        "max_yuan": 698000,
        "note": "可选说明"
      },
      "display_content": [
        {
          "type": "pdf",
          "file_name": "报告文件名.pdf",
          "file_url": "https://..."
        }
      ]
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
- `project_name`、`customer_name`、`support_type` 存在。
- `requirement_desc` 存在，且包含报告要求/客户需求。
- `display_content` 存在，没有附件时为空数组。
- 没有 JSON 外的解释文本。
