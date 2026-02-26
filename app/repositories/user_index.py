from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


class UserIndexRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    last_fact_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
            if "timezone" in cols:
                # legacy column, ignored by new UX
                pass

    def ensure_user(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))

    def all_users(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return list(conn.execute("SELECT * FROM users"))

    def set_last_fact_at(self, user_id: int, dt: datetime) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE users SET last_fact_at = ? WHERE user_id = ?", (dt.isoformat(), user_id))
