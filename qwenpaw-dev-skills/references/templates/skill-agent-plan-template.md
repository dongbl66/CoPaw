# <场景名称>Skill / Agent 实现计划模板

## 1. Skill 列表

| Skill | 类型 | 是否输出 structured_result |
|-------|------|----------------------------|
|       | 过程辅助型 / 报告输出型 / 工具调用型 | 是 / 否 |

## 2. 过程辅助型 Skill

要求：

- 不输出 JSON
- 不输出 structured_result
- 输出自然语言建议
- 明确输入和输出格式

## 3. 报告输出型 Skill

要求：

- 输出标准 `StructuredResultEvent`
- `result.type = business`
- `payload.scene = <scene>_report`
- `meta.bizModule = <scene>`
- 不新增不兼容协议

## 4. Agent

```text
agent id:
默认技能:
parser import path:
```

output binding：

```json
{
  "output_binding": {
    "final_output_parser_import_path": "backend.scenes.<scene>.parsers.<parser>:<function>"
  }
}
```

同时必须更新：

```text
.qwenpaw/workspaces/<scene>_agent/skill.json
.qwenpaw/config.json
```

`.qwenpaw/config.json` 只追加 `agents.agent_order` 与 `agents.profiles.<scene>_agent`，不要删除已有 Agent，不要修改 `active_agent`，除非用户明确要求。

## 5. 样例输入输出

输入：

```text

```

输出：

```json

```
