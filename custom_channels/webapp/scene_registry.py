# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class UnknownSceneError(KeyError):
    """Raised when a requested webapp scene is not configured."""


SCENES_DIR = Path(__file__).with_name("scenes")


@lru_cache(maxsize=1)
def load_scenes() -> dict[str, dict[str, Any]]:
    scenes: dict[str, dict[str, Any]] = {}
    if not SCENES_DIR.is_dir():
        return scenes
    for path in sorted(SCENES_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        scene_name = str(payload.get("scene") or path.stem)
        scenes[scene_name] = payload
    return scenes


class SceneRegistry:
    """Configuration registry for H5 webapp scenes."""

    def __init__(self) -> None:
        self._scenes = load_scenes()

    def get(self, scene: str) -> dict[str, Any]:
        if scene not in self._scenes:
            raise UnknownSceneError(f"Unknown scene: {scene}")
        return self._scenes[scene]

