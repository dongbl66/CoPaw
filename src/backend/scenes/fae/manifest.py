"""FAE 政企项目商机分析模块声明。"""

from backend.core.registry import register_backend_module
from backend.core.types import BackendModuleManifest
from backend.scenes.fae.router import create_router
from backend.scenes.fae.unified_router import create_router as create_unified_router

manifest = BackendModuleManifest(
    module_id="fae",
    name="FAE政企商机模块",
    version="0.1.0",
    router_factories=[create_router, create_unified_router],
)

register_backend_module(manifest)
