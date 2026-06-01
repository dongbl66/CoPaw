"""营销业务模块声明。"""

from backend.core.registry import register_backend_module
from backend.core.types import BackendModuleManifest
from backend.scenes.marketing.router import create_router

manifest = BackendModuleManifest(
    module_id="marketing",
    name="营销模块",
    version="0.1.0",
    router_factories=[create_router],
)

register_backend_module(manifest)
