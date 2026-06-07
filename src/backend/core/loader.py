"""内置业务后端模块加载器。"""

from importlib import import_module


_BUILTIN_BACKEND_MODULE_MANIFESTS = (
    "backend.scenes.marketing.manifest",
    "backend.scenes.fae.manifest",
    "backend.scenes.fraud_transcript.manifest",
)


def load_builtin_backend_modules() -> None:
    """通过导入副作用注册内置业务模块。"""
    for module_name in _BUILTIN_BACKEND_MODULE_MANIFESTS:
        module = import_module(module_name)
        register = getattr(module, "register", None)
        if callable(register):
            register()
