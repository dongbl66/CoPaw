# -*- coding: utf-8 -*-
"""Tests for backend module discovery and registration."""

from __future__ import annotations

import importlib

from fastapi import APIRouter


def test_load_builtin_backend_modules_registers_marketing_manifest() -> None:
    """Built-in backend loader should register the marketing scene module."""

    registry = importlib.import_module("backend.core.registry")
    loader = importlib.import_module("backend.core.loader")

    registry._MODULES.clear()

    loader.load_builtin_backend_modules()

    modules = registry.get_backend_modules()
    assert [module.module_id for module in modules] == ["marketing"]

    router = modules[0].router_factories[0]()
    assert isinstance(router, APIRouter)
    paths = {route.path for route in router.routes}
    assert "/api/backend/marketing/health" in paths
