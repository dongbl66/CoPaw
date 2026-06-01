"""业务后端模块类型定义。"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class BackendModuleManifest:
    """定义业务后端模块的挂载信息。"""

    module_id: str
    name: str
    version: str
    enabled_by_default: bool = True
    router_factories: list[Callable] = field(default_factory=list)
