---
name: qwenpaw-dev-api-contract-zh
description: 用于 QwenPaw/CoPaw 项目内需求说明书和原型已确认，需要定义前后端接口、DTO、错误语义或结构化结果合同时。
metadata:
  qwenpaw:
    emoji: "📡"
---

# QwenPaw 项目 API 合同技能

> 新业务场景 API 合同必须先读取 `../references/business-workbench-agent-standard.md`，并同时定义后端业务 API、`structured_result` 合同、latest/save/list/detail 接口、`payload.scene`、`meta.bizModule` 和 ResultWorkbench 消费方式。

## 触发条件

当需求说明书和 HTML 原型已经确认，需要进入前后端并行开发时，使用本技能。

## 输入

- 已确认的需求说明书
- 已确认的 HTML 原型
- 当前项目目录与既有模块模式

## 工作流程

1. 从页面与交互中提取 API 需求
2. 判断接口落点：核心路由还是插件路由
3. 定义请求 / 响应 DTO
4. 定义错误码与状态码
5. 判断是否需要结构化输出 schema / parser
6. 输出完整合同文档

## 输出格式

### 一、模块边界

```text
模块名: <module_name>
归属: 核心项目 / 插件 <plugin_name>
路由前缀: /api/<module_name> 或 /api/plugins/<plugin_name>/<module_name>
认证要求: 复用当前控制台登录态 / Agent 内部使用 / 无认证
```

### 二、接口清单

| HTTP 方法 | 端点 | 功能 | 代码落点 |
|-----------|------|------|----------|
| GET | `/api/<module_name>` | 列表 | `src/qwenpaw/app/routers/...` 或插件 router |
| POST | `/api/<module_name>` | 创建 / 触发动作 | 同上 |
| GET | `/api/<module_name>/{id}` | 详情 | 同上 |
| PATCH / PUT | `/api/<module_name>/{id}` | 更新 | 同上 |
| DELETE | `/api/<module_name>/{id}` | 删除 | 同上 |

### 三、请求 / 响应 DTO

先给出 Pydantic DTO，再给出 TypeScript 对应类型。

### 四、状态码与错误

至少明确：

- 参数校验失败
- 权限不足
- 资源不存在
- 冲突
- 内部错误

### 五、结构化输出边界

如果需求涉及 Agent 默认结构化输出，必须明确：

- `structured_model_import_path` 指向哪个 `BaseModel`
- 是否需要 `final_output_parser_import_path`
- parser 会往消息 metadata 注入什么字段
- Console 是否需要消费 `structured_result`

### 六、前端映射

| 前端页面 / 组件 | API | 调用时机 |
|----------------|-----|----------|
| 页面初始化 | GET | 首次加载 |
| 表单提交 | POST / PUT | 提交 |
| 结果面板 | 结构化输出 / 轮询接口 | 响应完成后 |

## 项目特定约束

- 不再沿用旧项目的 `src/backend/scenes/...` 作为默认落点
- 核心路由默认优先考虑 `src/qwenpaw/app/routers/`
- 插件路由优先考虑 `plugins/bundle/<plugin_name>/router.py` 或 `routers/`
- 结构化输出不是普通 JSON 文本，而是项目内绑定链路的一部分

## 新业务场景 API 合同要求

当需求被判定为新业务场景时，API 合同必须同时覆盖后端业务 API 和智能体结构化结果合同。

详细参考：

- `../references/new-business-scene.md`
- `../references/structured-result-contract.md`
- `../references/new-scene-delivery-package.md`
- `../references/templates/api-contract-template.md`

必须明确：

- API 前缀是否为 `/api/backend/<scene>`
- 是否需要 `/results/latest?session_id=...`
- 是否复用 `StructuredResultEvent`
- `result.type` 是什么
- `payload.scene` 是什么
- `meta.bizModule` 是什么
- 前端 ResultPanel 如何消费该结果

## 确认门

开发者未确认 API 合同，不进入实现阶段。
