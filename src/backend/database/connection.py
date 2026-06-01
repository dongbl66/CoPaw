# -*- coding: utf-8 -*-
"""Shared SQLite database access for backend business modules."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from qwenpaw.constant import WORKING_DIR


class BackendDatabase:
    """Provide SQLite connections and schema initialization."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        resolved_path = Path(db_path) if db_path is not None else (
            Path(WORKING_DIR) / "data" / "backend.sqlite3"
        )
        self._db_path = resolved_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    @property
    def db_path(self) -> Path:
        """Return the current SQLite database path."""

        return self._db_path

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Open a transactional SQLite connection."""

        self.initialize()
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Initialize required backend tables once."""

        if self._initialized:
            return

        with sqlite3.connect(self._db_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS marketing_opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    opportunity_type TEXT,
                    region TEXT,
                    source TEXT,
                    publish_time TEXT,
                    deadline TEXT,
                    credibility REAL,
                    contact TEXT,
                    budget REAL,
                    purchase_amount REAL,
                    link_status TEXT,
                    reason TEXT,
                    original_link TEXT,
                    level TEXT,
                    summary TEXT,
                    session_id TEXT,
                    agent_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """,
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS marketing_product_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    save_status TEXT NOT NULL DEFAULT 'draft',
                    scene TEXT,
                    summary TEXT,
                    detail_content_json TEXT NOT NULL,
                    info_json TEXT NOT NULL,
                    basic_info_json TEXT NOT NULL,
                    product_info_json TEXT NOT NULL,
                    session_id TEXT,
                    agent_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """,
            )
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(marketing_product_results)",
                ).fetchall()
            }
            if "save_status" not in columns:
                connection.execute(
                    """
                    ALTER TABLE marketing_product_results
                    ADD COLUMN save_status TEXT NOT NULL DEFAULT 'draft'
                    """,
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS marketing_result_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    mime_type TEXT,
                    file_url TEXT,
                    preview_url TEXT,
                    download_url TEXT,
                    file_path TEXT,
                    file_id TEXT,
                    file_size INTEGER,
                    page_index INTEGER,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    source_type TEXT,
                    extra_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(result_id) REFERENCES marketing_product_results(id)
                    ON DELETE CASCADE
                )
                """,
            )
            connection.commit()

        self._initialized = True


_backend_database: BackendDatabase | None = None


def get_backend_database() -> BackendDatabase:
    """Return the shared backend database instance."""

    global _backend_database
    if _backend_database is None:
        _backend_database = BackendDatabase()
    return _backend_database
