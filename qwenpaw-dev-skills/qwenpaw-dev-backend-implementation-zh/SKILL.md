---
name: qwenpaw-dev-backend-implementation-zh
description: 用于 QwenPaw/CoPaw 项目内 API 合同已确认，需要实现后端路由、配置、Agent 绑定、parser、hook、persistence 或插件后端时。
metadata:
  qwenpaw:
    emoji: "🧩"
---

# QwenPaw 项目后端实现技能

> 新业务场景后端实现必须先读取 `../references/business-workbench-agent-standard.md`，并实现 scene manifest、parser、hook、persistence、repository、service、router；不要为了单个场景修改 `react_agent.py`。

## 触发条件

当 API 合同已确认，需要在 QwenPaw/CoPaw 中实现后端能力时，使用本技能。

## 输入

- 已确认的 API 合同
- 需求说明书
- 是否涉及 Agent、Skill、Plugin、结构化输出

## 先做归类

在写代码前，先判断需求属于哪一类：

1. `HTTP/API 能力`
   - 落点通常在 `src/qwenpaw/app/routers/`
   - 或插件 `plugins/bundle/<plugin_name>/router.py` / `routers/`
2. `Agent 运行时能力`
   - 落点通常在 `src/qwenpaw/agents/`
3. `配置模型或 agent.json 绑定能力`
   - 落点通常在 `src/qwenpaw/config/config.py`
4. `插件后端能力`
   - 落点通常在 `plugins/bundle/<plugin_name>/plugin.py`、`hooks.py`、`tools/`、`modules/`

不要默认套用旧项目的 `src/backend/scenes/...` 或 `DDD workflow/service/entity` 目录。

## 工作流程

1. 明确代码落点与边界
2. 定义或扩展 Pydantic 模型
3. 实现路由 / 解析 / 绑定逻辑
4. 如涉及 Agent，补齐 `output_binding` 或 parser
5. 如涉及插件，补齐 plugin backend 集成
6. 编写对应测试

## 典型实现模式

### 1. 核心路由

适用于本项目主后端 API：

- 文件位置：`src/qwenpaw/app/routers/<module>.py`
- 常见内容：
  - `APIRouter`
  - 请求 / 响应 `BaseModel`
  - 对 `config`、workspace、git、skills、agent 管理能力的调用

### 2. Agent / 输出绑定

如果需求不是普通 API，而是“让某个 Agent 默认输出结构化结果”，优先查看：

- `src/qwenpaw/agents/output_binding.py`
- `src/qwenpaw/config/config.py`
- `src/qwenpaw/agents/react_agent.py`
- `src/qwenpaw/app/channels/console/structured_result_event.py`

此时实现重点不在路由，而在以下链路：

1. 定义 `BaseModel` schema
2. 通过 `AgentOutputBindingConfig` 绑定 `structured_model_import_path`
3. 如需要，绑定 `final_output_parser_import_path`
4. 由 parser 向最终消息 metadata 注入结构化结果
5. 如果 Console 需要实时消费，保证 metadata 兼容 `structured_result` 事件

### 3. 插件后端

适用于 bundle 级能力：

- `plugins/bundle/<plugin_name>/plugin.py`
- `plugins/bundle/<plugin_name>/router.py` 或 `routers/*.py`
- `plugins/bundle/<plugin_name>/hooks.py`
- `plugins/bundle/<plugin_name>/tools/*.py`
- `plugins/bundle/<plugin_name>/modules/*`

插件启动逻辑保持轻量，只做注册、挂载、注入，不做重型业务执行。

## 结构化输出实现要求

当需求涉及结构化输出时，必须显式回答：

- schema 定义在哪个模块
- import path 是什么
- 是否作为 agent 默认结构化模型
- parser 是否只做补充元数据，还是承担文本转结构化对象
- Console / Channel 是否需要识别该结构

不要把“结构化输出”写成“让模型返回一段 JSON 字符串”就结束。

## 通用约束

- 路由层只做参数接收、调用、响应封装
- 配置模型变更必须与 `AgentProfileConfig` / `AgentsConfig` 现有结构兼容
- 涉及 agent.json 的能力，优先复用现有配置与加载逻辑
- 插件能力优先参考 `cloudpaw` 与 `qwenpaw-pet` 的现有模式
- 测试至少覆盖新增 DTO、解析逻辑或关键分支

## 参考

- `references/backend-implementation.md`
- `references/structured-output-binding.md`

## 新业务场景后端实现要求

当需求被判定为新业务场景，并且包含结构化报告、结果沉淀、历史列表、详情页或业务工作台时，不要只实现单个核心路由或孤立 parser。必须参考现有 `marketing` / `fae` 场景，设计完整后端链路。

详细参考：

- `../references/new-business-scene.md`
- `../references/hook-registry.md`
- `../references/structured-result-contract.md`
- `../references/new-scene-delivery-package.md`
- `../references/templates/backend-scene-plan-template.md`

推荐落点：

- 业务场景模块：`src/backend/scenes/<scene>/`
- manifest：`src/backend/scenes/<scene>/manifest.py`
- router：`src/backend/scenes/<scene>/router.py`
- schemas：`src/backend/scenes/<scene>/schemas/`
- parser：`src/backend/scenes/<scene>/parsers/`
- hook：`src/backend/scenes/<scene>/hooks/`
- persistence：`src/backend/scenes/<scene>/persistence.py`
- service / repository：`service.py`、`repository.py`
- loader 注册：`src/backend/core/loader.py`
- hook registry：`src/backend/core/business_hooks.py`

实现方案必须显式说明：

- `final_output_parser_import_path` 指向哪里
- parser 如何把模型文本转为 `msg.metadata["structured_result"]`
- hook 的 `should_handle` 如何避免误处理其他业务场景
- 持久化表或复用表的选择理由
- 业务 API 的路径前缀，例如 `/api/backend/<scene>`
- 是否需要最新结果接口，例如 `/results/latest?session_id=...`
- 是否完全通过 `backend.scenes.<scene>.manifest` 注册 hook factory，避免场景代码侵入 `react_agent.py`

注意：`src/backend/scenes/<scene>/` 只用于明确的新业务场景。普通核心能力仍优先落在 `src/qwenpaw/app/routers/`，不能把所有后端需求都泛化成 scenes。
