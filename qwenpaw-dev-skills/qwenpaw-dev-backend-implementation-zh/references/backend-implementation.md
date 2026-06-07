# QwenPaw 后端实现参考

## 常见落点

- 核心 API 路由：`src/qwenpaw/app/routers/`
- Agent 能力：`src/qwenpaw/agents/`
- 配置模型：`src/qwenpaw/config/config.py`
- 插件 bundle：`plugins/bundle/<plugin_name>/`

## 判断顺序

1. 这是普通 HTTP 能力吗？
2. 这是 Agent 输出或行为能力吗？
3. 这是配置模型能力吗？
4. 这是插件 bundle 能力吗？

## 不建议继续默认使用的旧路径

- `src/backend/scenes/...`
- 通用 `application/core/models/database` 四层模板

这些路径可能适合旧项目，但不是当前仓库的主后端入口。

## 推荐实现姿势

- 先找最接近的现有文件，再沿用模式
- 路由优先放到 `app/routers`
- Agent 输出绑定优先复用 `output_binding`
- 插件优先复用现有 `plugin.py + router/hooks/tools/modules` 结构
