# Structured Result 合同参考

> 新业务场景还必须读取 `business-workbench-agent-standard.md`。`structured_result` 不只是展示合同，还要支撑 ResultWorkbench 自动显示、后端持久化、保存列表和详情页。

## 1. 基本原则

新业务场景必须优先复用项目现有 `StructuredResultEvent`，不要随意新增不兼容协议。

推荐：

```text
eventType = structured_result
result.type = business
payload.scene = <scene>_report
meta.bizModule = <scene>
```

## 2. 标准结构

```json
{
  "eventType": "structured_result",
  "version": "1.0",
  "title": "<报告标题>",
  "subtitle": "<报告副标题>",
  "result": {
    "type": "business",
    "payload": {
      "title": "<报告标题>",
      "summary": "<摘要>",
      "scene": "<scene>_report",
      "basicInfo": {},
      "productInfo": {},
      "opportunities": [],
      "attachments": []
    }
  },
  "layout": {
    "autoOpen": true,
    "replace": true,
    "panelWidth": 640
  },
  "meta": {
    "bizModule": "<scene>",
    "source": "skill",
    "timestamp": 0
  }
}
```

## 3. 字段使用约定

| 字段 | 用途 |
|------|------|
| `basicInfo` | 基础信息、关键字段、主体信息 |
| `productInfo` | 分析详情、评分、路径、结论 |
| `opportunities` | 可重复条目，常用于问题答案、发现项、风险项 |
| `attachments` | 文件、PDF、HTML、图片等附件 |

## 4. ResultPanel 分流

前端优先通过 `payload.scene` 分流：

```ts
if (
  result.result.type === "business" &&
  payload.scene === "<scene>_report"
) {
  return <<Scene>Report payload={payload} />;
}
```

当业务需要右侧工作台、保存或历史列表时，不要把逻辑继续堆在通用 ResultWorkbench fallback 中。应在业务 manifest 中注册 `resultWorkbench`，并将业务加载、保存、详情跳转逻辑放入 `console/src/business/<scene>/workbench/`。

## 5. 何时允许扩展 result.type

只有满足以下条件，才允许扩展 `StructuredResultType`：

- 现有 `business` / `product` / `table` / `text` / `html` 无法承载
- 该类型具有跨多个业务场景复用价值
- 已同步更新 ResultPanel renderer
- 已补充类型、测试和迁移说明

单个业务场景不应为了自身方便随意新增 `result.type`。
