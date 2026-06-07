# QwenPaw 结构化输出绑定参考

## 目标

把“模型输出结构化结果”落到项目真实链路，而不是停留在提示词层。

## 关键部件

### 1. schema

使用 Pydantic `BaseModel` 定义结构化输出模型。

### 2. Agent 配置绑定

`src/qwenpaw/config/config.py` 中的 `AgentOutputBindingConfig` 支持：

- `structured_model_import_path`
- `final_output_parser_import_path`

### 3. 运行时解析

`src/qwenpaw/agents/output_binding.py` 负责把 import path 解析成：

- `structured_model`
- `final_output_parser`

### 4. Agent 默认输出

`src/qwenpaw/agents/react_agent.py` 中，Agent 支持：

- `default_structured_model`
- `final_output_parser`

注意：这里的 `react_agent.py` 是通用运行时机制参考，不是新业务场景的注册点。新场景需要 post-reply hook 时，应通过 `backend.scenes.<scene>.manifest` 注册 hook factory，并由通用 hook registry 被 `react_agent.py` 读取。

### 5. Console 事件消费

`src/qwenpaw/app/channels/console/structured_result_event.py` 会从消息 metadata 中提取：

- `structured_result`
- 其中 `eventType` 需要是 `structured_result`

## 实现检查清单

- schema 是否真的是 `BaseModel` 子类
- import path 是否可解析
- parser 是否可调用
- parser 注入的 metadata 结构是否稳定
- Console 是否真的需要消费该结构化结果

## 常见误区

- 只让模型“输出 JSON 文本”，但没有绑定 schema
- parser 把结构化数据藏在任意字段里，Console 无法识别
- 把结构化输出逻辑塞进路由层，而不是绑定到 Agent 输出链路
- 为每个新业务场景修改一次 `react_agent.py`，而不是使用 hook registry
