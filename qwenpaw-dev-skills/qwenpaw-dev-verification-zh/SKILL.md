---
name: qwenpaw-dev-verification-zh
description: 用于 QwenPaw/CoPaw 项目内前端、后端、Skill、Agent、插件或新业务场景实现完成后需要真实验证 ResultWorkbench、保存列表、详情页、结构化结果或端到端链路时。
metadata:
  qwenpaw:
    emoji: "✅"
---

# QwenPaw 项目验证技能

> 新业务场景验证必须先读取 `../references/business-workbench-agent-standard.md`，并验证聊天 JSON 自动打开右侧 Workbench、刷新只拉当前 bizModule、保存可回查 latest、保存列表刷新、详情页可打开。

## 触发条件

当需求对应的实现已经完成，需要给出真实验证结果而不是口头完成结论时，使用本技能。

## 输入

- 已完成的代码改动
- 对应的目标目录
- 可以执行的本地命令

## 工作流程

1. 汇总本次变更文件
2. 判断需要验证的子系统
3. 运行对应命令
4. 记录通过项、失败项、跳过项
5. 输出未验证风险

## 常见验证命令

### Python / 后端

```bash
python -m pytest
```

如果范围较小，优先跑目标测试目录或文件。

### Console

```bash
cd console
npm run lint
npm run test:run
npm run build
```

### Website

按 `website/package.json` 的实际命令执行相应 lint / build / test。

### 插件前端

进入对应 `ui/` 或 `frontend/` 目录，执行该插件实际脚本。

## 必检内容

### 前端

- 页面是否可访问
- API 调用是否符合合同
- i18n、加载态、错误态是否合理

### 后端

- 路由是否注册成功
- 请求 / 响应模型是否匹配
- 配置变更是否兼容现有加载逻辑

### 结构化输出

- schema 是否可解析
- parser 是否可执行
- metadata 是否产出预期结构
- 若 Console 依赖 `structured_result`，是否符合事件形态

### 技能 / Agent

- 技能目录是否完整
- frontmatter 是否可读
- Agent 绑定是否指向有效 import path

### 插件

- `plugin.json` 是否完整
- backend / frontend entry 是否存在
- 目录结构是否与插件模式一致

## 输出要求

- 列出执行过的命令
- 列出通过项
- 列出失败项
- 列出未执行项与原因
- 列出未验证风险

## 新业务场景验证要求

当需求被判定为新业务场景时，必须按统一检查表进行验证。

详细参考：

- `../references/new-scene-checklist.md`
- `../references/new-scene-delivery-package.md`
- `../references/templates/verification-template.md`

必须覆盖：

- parser 单测
- hook 单测
- persistence 单测
- router 单测
- ResultPanel renderer 测试
- business 页面测试
- Skill 输出检查
- 端到端 smoke test
