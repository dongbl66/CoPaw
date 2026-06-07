# <场景名称>API 合同模板

## 1. 模块边界

```text
模块名称：
归属：
API 前缀：
认证要求：
参考场景：
```

## 2. 接口清单

| 方法 | 端点 | 功能 | 代码落点 |
|------|------|------|----------|
| GET | `/api/backend/<scene>/health` | 健康检查 | `router.py` |
| GET | `/api/backend/<scene>/results` | 结果列表 | `router.py` |
| GET | `/api/backend/<scene>/results/latest` | 最新结果 | `router.py` |
| GET | `/api/backend/<scene>/results/{id}` | 结果详情 | `router.py` |
| POST | `/api/backend/<scene>/results/{id}/save` | 保存结果 | `router.py` |

## 3. DTO

### 后端 Pydantic

```python
class <Scene>ResultRead(BaseModel):
    ...
```

### 前端 TypeScript

```ts
export interface <Scene>ResultRecord {
  ...
}
```

## 4. 结构化结果合同

```text
eventType = structured_result
result.type = business
payload.scene = <scene>_report
meta.bizModule = <scene>
```

## 5. 错误码

- 400 参数错误
- 401 未认证
- 403 无权限
- 404 资源不存在
- 409 状态冲突
- 500 内部错误

## 6. 前端映射

| 前端模块 | API | 调用时机 |
|----------|-----|----------|
| ResultWorkbench | structured_result + latest result | Chat 完成后自动打开右侧业务页 |
| ResultPanel | structured_result | Workbench 内部渲染报告 |
| Results 页面 | list results | 页面加载 |
| Detail 页面 | get result | 进入详情 |

保存合同必须说明：当 Workbench 只有 direct JSON、没有 active record 时，前端先按 `session_id + meta.bizModule` 调用 latest，再调用 save。
