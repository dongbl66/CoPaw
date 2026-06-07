# <场景名称>后端实现计划模板

## 1. 目标

- 

## 2. 文件落点

```text
src/backend/scenes/<scene>/
  manifest.py
  router.py
  service.py
  repository.py
  persistence.py
  dependencies.py
  exceptions.py
  schemas/
  parsers/
  hooks/
```

## 3. Manifest

- 注册 backend module
- 注册 hook factory
- 保证重复加载幂等

## 4. Parser

```text
import path:
backend.scenes.<scene>.parsers.<parser>:<function>
```

职责：

- 提取模型输出
- 校验 structured_result
- 写入 metadata

## 5. Hook

- should_handle 条件：
- 持久化前二次校验：
- persistence 调用：

## 6. Persistence

表：

```text
<scene>_results
```

字段：

- id
- title
- result_type
- scene
- summary
- info_json
- structured_result_json
- session_id
- agent_id
- created_at
- updated_at

## 7. Router

```text
GET  /api/backend/<scene>/results
GET  /api/backend/<scene>/results/latest
GET  /api/backend/<scene>/results/{id}
POST /api/backend/<scene>/results/{id}/save
```

如项目存在统一结果入口，还要支持：

```text
GET /api/backend/results/latest?session_id=<id>&biz_module=<scene>
```

## 8. 测试

- parser
- hook
- persistence
- router
- manifest loading
