---
name: qwenpaw-dev-skill-agent-construction-zh
description: 用于 QwenPaw/CoPaw 项目内新增业务 Agent、业务 Skill、skill.json、agent.json、output_binding 或结构化输出链路时。
metadata:
  qwenpaw:
    emoji: "🤖"
---

# QwenPaw 业务 Agent 与技能构建

> 新业务场景 Skill/Agent 构建必须先读取 `../references/business-workbench-agent-standard.md`。业务专属 Skill 先按业务逻辑拆分，再放入 `.qwenpaw/workspaces/<agent_id>/skills/`；创建 workspace Agent 后必须同步 `skill.json`、`agent.json` 和项目根目录 `.qwenpaw/config.json`。

## 核心原则

新业务场景优先创建“工作区级业务 Agent”，再把该业务需要的技能放进这个 Agent 的 `skills/` 目录。不要把业务专属技能直接放到全局 `src/qwenpaw/agents/skills/`。

参考结构：`.qwenpaw/workspaces/RA-agent/`

## 标准流程

1. 分析业务逻辑：确认用户角色、输入来源、处理步骤、最终交付物、是否需要结构化结果。
2. 拆分技能职责：按业务步骤拆成一个或多个 Skill，明确每个 Skill 是过程辅助、报告输出还是工具调用。
3. 执行 skill-create 思路：为每个 Skill 写 `SKILL.md`，包含稳定触发描述、业务流程、输入输出、禁止事项和验证点。
4. 创建 workspace Agent：在 `.qwenpaw/workspaces/<agent_id>/` 下创建独立智能体目录。
5. 放置技能：把业务技能放到 `.qwenpaw/workspaces/<agent_id>/skills/<skill_name>/SKILL.md`。
6. 配置技能清单：创建或更新 `.qwenpaw/workspaces/<agent_id>/skill.json`。
7. 配置智能体：创建或更新 `.qwenpaw/workspaces/<agent_id>/agent.json`，必要时补充 `PROFILE.md`、`SOUL.md`、`BOOTSTRAP.md`。
8. 注册智能体：更新项目根目录 `.qwenpaw/config.json` 的 `agents.agent_order` 与 `agents.profiles`。
9. 绑定输出链路：如果有结构化报告，补齐 `output_binding`、parser、hook、ResultPanel 和持久化逻辑。
10. 验证：检查 JSON、Skill frontmatter、目录路径、Agent 可发现性和结构化输出链路。

## 落点判断

| 场景 | 正确落点 |
| --- | --- |
| 业务专属 Agent 的技能 | `.qwenpaw/workspaces/<agent_id>/skills/<skill_name>/SKILL.md` |
| 工作区级业务 Agent | `.qwenpaw/workspaces/<agent_id>/` |
| 可复用的项目内置通用技能 | `src/qwenpaw/agents/skills/<skill_name>/SKILL.md` |
| 插件 bundle 专属技能 | `plugins/bundle/<plugin_name>/skills/<skill_name>/SKILL.md` |
| 插件 Agent 模板 | `plugins/bundle/<plugin_name>/agents/` |

业务专属技能不得放入 `src/qwenpaw/agents/skills/`，除非它已经被明确设计为跨业务、跨 Agent 复用的产品内置技能。

## Workspace Agent 目录

创建业务 Agent 时，使用 RA-agent 风格目录：

```text
.qwenpaw/workspaces/<agent_id>/
+-- agent.json
+-- skill.json
+-- PROFILE.md
+-- SOUL.md
+-- BOOTSTRAP.md
+-- skills/
    +-- <skill_one>/
    |   +-- SKILL.md
    +-- <skill_two>/
        +-- SKILL.md
```

`agent_id` 使用稳定英文、数字、连字符或下划线，必须和 `agent.json.id`、`.qwenpaw/config.json` 中的 profile key 保持一致。

## Skill 创建要求

每个业务 Skill 都必须先写清楚业务职责，再写执行步骤。

`SKILL.md` 必须包含：

- frontmatter：`name` 与 `description`，`description` 要能根据用户请求稳定触发。
- 业务定位：这个 Skill 解决哪个业务步骤。
- 输入：用户会提供什么材料、文件或上下文。
- 流程：按业务逻辑顺序说明如何处理。
- 输出：自然语言建议、结构化报告、工具调用结果三选一或组合，但必须明确定义。
- 禁止事项：例如过程辅助型 Skill 不输出 JSON，报告型 Skill 不绕过 parser/hook/ResultPanel。
- 验证点：说明完成后如何检查结果是否可用。

同一业务 Agent 可以有多个 Skill，但要避免职责重叠。一个 Skill 只负责一个清晰业务环节。

## Skill 类型

- 过程辅助型 Skill：只输出自然语言建议，不输出 `structured_result`。
- 报告输出型 Skill：输出项目兼容的 `StructuredResultEvent`，并走 parser、hook、ResultPanel 链路。
- 工具调用型 Skill：说明调用哪些工具、API 或 MCP，不承担最终展示协议。

如果一个业务既需要引导提问又需要生成报告，应拆成两个 Skill。例如：

- `<scene>-question-guide`：过程辅助型，负责追问、澄清、引导用户补充材料。
- `<scene>-extract-report`：报告输出型，负责抽取字段、形成结构化结果并交给输出链路。

## skill.json 示例

在 `.qwenpaw/workspaces/<agent_id>/skill.json` 中登记该 Agent 自己的技能：

```json
{
  "schema_version": "workspace-skill-manifest.v1",
  "version": 0,
  "skills": {
    "<skill_name>": {
      "enabled": true,
      "channels": ["all"],
      "source": "custom",
      "metadata": {
        "name": "<skill_name>",
        "description": "<与 SKILL.md frontmatter description 保持一致>",
        "version_text": "1.0",
        "source": "custom",
        "protected": false
      },
      "requirements": {
        "require_bins": [],
        "require_envs": []
      },
      "config": {}
    }
  }
}
```

新增多个技能时，全部写入同一个 `skills` map。

## agent.json 要求

`agent.json` 至少要明确：

- `id`：与目录名、config profile key 保持一致。
- `name`：终端用户可理解的智能体名称。
- `description`：说明该 Agent 的业务能力。
- `workspace_dir`：指向 `.qwenpaw/workspaces/<agent_id>`。
- `template_id`：通常沿用 `default`，除非已有专用模板。
- `channels`：按业务需要启用 `console`、`webapp` 等通道。
- `output_binding`：只有结构化输出场景需要。

如果业务需要在 Web 场景渲染，`channels.webapp.scene` 必须和前端 ResultPanel 使用的 `payload.scene` 一致。

## .qwenpaw/config.json 注册

创建工作区 Agent 后，必须更新项目根目录 `.qwenpaw/config.json`：

```json
{
  "agents": {
    "agent_order": ["default", "<agent_id>"],
    "profiles": {
      "<agent_id>": {
        "id": "<agent_id>",
        "workspace_dir": "E:\\programproject\\QwenpawPro\\CoPaw_new\\.qwenpaw\\workspaces\\<agent_id>",
        "enabled": true
      }
    }
  }
}
```

更新规则：

- `agents.agent_order` 中追加 `<agent_id>`，不要删除已有 Agent。
- `agents.profiles` 中新增同名 profile，key、`id`、目录名三者一致。
- `workspace_dir` 使用当前项目的真实绝对路径。
- 不要覆盖 `active_agent`，除非用户明确要求切换默认 Agent。

## 结构化输出链路

当 Skill 会产出报告、分析结果、结构化面板或历史结果时，必须确认：

详细参考：

- `../references/new-business-scene.md`
- `../references/structured-result-contract.md`
- `../references/new-scene-delivery-package.md`
- `../references/templates/skill-agent-plan-template.md`
- `../examples/fraud-transcript/README.md`

- 是否需要专用 Agent。
- 是否需要 `AgentProfileConfig.output_binding`。
- 是否需要 `final_output_parser_import_path`。
- parser 是否落在 `src/backend/scenes/<scene>/parsers/`。
- hook 是否落在 `src/backend/scenes/<scene>/hooks/`。
- 是否需要写入 `msg.metadata["structured_result"]`。
- 是否需要持久化到业务场景结果表。
- ResultPanel 通过哪个 `payload.scene` 渲染。

不要让过程辅助型 Skill 输出 JSON，也不要让报告输出型 Skill 绕过 parser、hook、ResultPanel 链路。

## 验证清单

- `agent.json` 是合法 JSON，且 `id`、目录名、config profile key 一致。
- `skill.json` 是合法 JSON，且每个 skill entry 都能对应到 `skills/<skill_name>/SKILL.md`。
- 每个 `SKILL.md` frontmatter 合法，`name` 与目录名一致。
- `.qwenpaw/config.json` 是合法 JSON，且 `agents.agent_order` 与 `agents.profiles` 已注册新 Agent。
- 工作区技能没有误放到 `src/qwenpaw/agents/skills/`。
- 如有 `output_binding.final_output_parser_import_path`，对应 import path 可导入。
- 如有 Web 渲染，`payload.scene`、`channels.webapp.scene`、ResultPanel 分发值一致。
- 不要删除或覆盖用户已有 Agent、Skill 或 config 字段。

## 输出说明

完成方案或实现时，必须向用户说明：

- 新增 Agent 目录。
- 新增 Skill 列表及类型。
- 是否更新 `skill.json`。
- 是否更新 `agent.json`。
- 是否更新 `.qwenpaw/config.json`。
- 是否涉及 `output_binding`、parser、hook、ResultPanel 或持久化。
