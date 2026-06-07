---
name: qwenpaw-dev-plugin-integration-zh
description: 用于 QwenPaw/CoPaw 项目内新增能力需要接入 plugins/bundle 插件结构、插件路由、hooks、tools、skills 或 agents 时。
metadata:
  qwenpaw:
    emoji: "🧩"
---

# QwenPaw 项目插件集成技能

## 触发条件

当需求需要作为 bundle 插件交付，而不是直接并入核心项目时，使用本技能。

## 输入

- 已完成或已设计好的前端能力
- 已完成或已设计好的后端能力
- 已完成或已设计好的技能 / Agent

## 工作流程

1. 确认插件是否应该新建 bundle，还是扩展现有 bundle
2. 按现有插件模式组织目录
3. 编写或更新 `plugin.json`
4. 挂载 backend 与 frontend entry
5. 接入路由、hooks、tools、skills、agents
6. 做最小可用验证

## 推荐目录结构

```text
plugins/bundle/<plugin_name>/
├── plugin.json
├── plugin.py
├── router.py 或 routers/
├── hooks.py                # 可选
├── tools/                  # 可选
├── modules/                # 可选
├── skills/                 # 可选
├── agents/                 # 可选
├── ui/ 或 frontend/        # 可选，取决于插件既有模式
└── dist/ 或 ui/dist/       # 构建产物
```

## plugin.json 约束

优先参考现有 `cloudpaw` 和 `qwenpaw-pet`：

- 使用 `entry.backend`
- 如有前端，使用 `entry.frontend`
- 写明 `min_version`
- 只声明真实依赖

## 集成原则

- 插件启动逻辑保持轻量
- 路由、hook、tool、module 的职责分开
- 前端结构沿用该插件当前使用的 `ui/` 或 `frontend/` 目录，不混搭
- 插件技能放在 `skills/` 下
- 插件 Agent 模板放在 `agents/` 下

如果插件承载新业务场景，必须参考：

- `../references/new-business-scene.md`
- `../references/hook-registry.md`
- `../references/structured-result-contract.md`

并明确：

- 插件内业务能力是否需要后端 scene 等价结构
- 是否需要通过 manifest 注册 hook factory
- 是否需要复用主项目 ResultPanel 协议
- 插件 UI 与主 Console business 页面是否共存

## 何时不该做成插件

以下情况优先考虑核心项目改动，而不是插件：

- 明显属于全局控制台基础设施
- 明显属于所有 agent 的通用配置能力
- 明显属于主应用默认后端 API

## 输出要求

- 列出插件目录结构
- 说明 backend entry 与 frontend entry
- 说明是否需要技能 / Agent 模板
- 说明与主项目的接口边界
