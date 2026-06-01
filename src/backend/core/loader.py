"""内置业务后端模块加载器。"""


def load_builtin_backend_modules() -> None:
    """通过导入副作用注册内置业务模块。"""
    import backend.scenes.marketing.manifest  # noqa: F401
