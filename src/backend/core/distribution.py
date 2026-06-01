"""业务模块分发配置读取。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_DISTRIBUTION = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "distributions"
    / "digital-employee.json"
)


def load_distribution_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """读取当前发行版配置。"""
    target = Path(config_path) if config_path else _DEFAULT_DISTRIBUTION
    if not target.exists():
      return {}
    return json.loads(target.read_text(encoding="utf-8"))
