"""业务后端模块注册中心。"""

from .types import BackendModuleManifest

_MODULES: list[BackendModuleManifest] = []


def register_backend_module(manifest: BackendModuleManifest) -> None:
    """注册业务后端模块。"""
    _MODULES.append(manifest)


def get_backend_modules() -> list[BackendModuleManifest]:
    """返回所有已注册业务后端模块。"""
    return list(_MODULES)
