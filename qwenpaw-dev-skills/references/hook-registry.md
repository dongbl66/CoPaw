# Hook Registry 参考

## 1. 目标

新业务场景不应反复修改 `src/qwenpaw/agents/react_agent.py` 来注册自己的 post-reply hook。

正确做法：

```text
react_agent.py 只负责从 backend hook registry 读取 hook
backend.scenes.<scene>.manifest 负责注册自己的 hook factory
```

因此，新场景实施方案中如果出现“修改 `react_agent.py` 注册某个具体场景 hook”，应退回重写。只有通用 hook registry 机制不存在或需要升级时，才允许修改 `react_agent.py`。

## 2. 注册中心

核心文件：

```text
src/backend/core/business_hooks.py
```

应提供：

```python
register_business_post_reply_hook(factory)
get_business_post_reply_hooks()
get_business_post_reply_hook_factories()
```

注册应当是幂等的，重复加载 manifest 不应重复注册同一个 hook factory。

## 3. Manifest 注册模板

```python
from backend.core.business_hooks import register_business_post_reply_hook
from backend.core.registry import register_backend_module
from backend.core.types import BackendModuleManifest
from backend.scenes.<scene>.router import create_router


def create_<scene>_post_reply_hook():
    from backend.scenes.<scene>.hooks import <Scene>PostReplyHook

    return <Scene>PostReplyHook()


def register() -> None:
    register_backend_module(
        BackendModuleManifest(
            module_id="<scene>",
            name="<业务场景名称>",
            version="0.1.0",
            router_factories=[create_router],
        )
    )
    register_business_post_reply_hook(create_<scene>_post_reply_hook)


register()
```

## 4. 为什么 hook factory 要懒加载

manifest 在 backend loader 中会较早加载。

如果 manifest 顶层直接 import 具体 hook，可能提前拉起 Agent 侧依赖，造成循环依赖或测试环境导入失败。

推荐：

```python
def create_<scene>_post_reply_hook():
    from backend.scenes.<scene>.hooks import <Scene>PostReplyHook
    return <Scene>PostReplyHook()
```

不要：

```python
from backend.scenes.<scene>.hooks import <Scene>PostReplyHook
register_business_post_reply_hook(<Scene>PostReplyHook)
```

## 5. Hook should_handle 要求

每个业务 hook 必须避免误处理其他场景。

推荐同时检查：

- agent id
- parser import path
- `metadata.structured_result.meta.bizModule`
- `metadata.structured_result.result.payload.scene`

持久化前必须二次校验：

```text
meta.bizModule == <scene>
payload.scene == <scene>_report
```
