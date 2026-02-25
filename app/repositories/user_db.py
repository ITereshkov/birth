from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from app.models.entities import TxType, UserProfile


class UserRepository:
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
                CREATE TABLE IF NOT EXISTS profile (
                    user_id INTEGER PRIMARY KEY,
                    timezone TEXT NOT NULL DEFAULT 'Europe/Moscow',
                    currency TEXT NOT NULL DEFAULT 'RUB',
                    premium_until TEXT,
                    notifications_enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, type)
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL,
                    happened_at TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def ensure_profile(self, user_id: int, timezone: str = "Europe/Moscow") -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO profile(user_id, timezone) VALUES(?, ?)",
                (user_id, timezone),
            )

    def get_profile(self, user_id: int) -> UserProfile:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM profile WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            self.ensure_profile(user_id)
            return self.get_profile(user_id)
        premium_until = (
            datetime.fromisoformat(row["premium_until"]) if row["premium_until"] else None
        )
        return UserProfile(
            user_id=row["user_id"],
            timezone=row["timezone"],
            currency=row["currency"],
            premium_until=premium_until,
            notifications_enabled=bool(row["notifications_enabled"]),
        )

    def update_timezone(self, user_id: int, timezone: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE profile SET timezone = ? WHERE user_id = ?", (timezone, user_id))

    def set_premium_until(self, user_id: int, premium_until: datetime) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE profile SET premium_until = ? WHERE user_id = ?",
                (premium_until.isoformat(), user_id),
            )

    def add_category(self, name: str, tx_type: TxType) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO categories(name, type) VALUES(?, ?)",
                (name.lower(), tx_type.value),
            )

    def category_exists(self, name: str, tx_type: TxType) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM categories WHERE name = ? AND type = ?",
                (name.lower(), tx_type.value),
            ).fetchone()
        return bool(row)

    def add_transaction(
        self,
        amount: float,
        category: str,
        tx_type: TxType,
        happened_at: datetime,
        comment: str | None = None,
    ) -> int:
        self.add_category(category, tx_type)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO transactions(amount, category, type, happened_at, comment)
                VALUES(?, ?, ?, ?, ?)
                """,
                (amount, category.lower(), tx_type.value, happened_at.isoformat(), comment),
            )
            return int(cursor.lastrowid)

    def month_tx_count(self, year: int, month: int) -> int:
        start = datetime(year, month, 1)
        end = datetime(year + (month // 12), (month % 12) + 1, 1)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM transactions WHERE happened_at >= ? AND happened_at < ?",
                (start.isoformat(), end.isoformat()),
            ).fetchone()
        return int(row["cnt"])

    def get_transactions(self, start: datetime, end: datetime) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, amount, category, type, happened_at, comment
                FROM transactions
                WHERE happened_at >= ? AND happened_at < ?
                ORDER BY happened_at ASC
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return list(rows)

    def has_transactions_on_date(self, check_date: datetime) -> bool:
        start = datetime(check_date.year, check_date.month, check_date.day)
        end = start + timedelta(days=1)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM transactions WHERE happened_at >= ? AND happened_at < ? LIMIT 1",
                (start.isoformat(), end.isoformat()),
            ).fetchone()
        return bool(row)
