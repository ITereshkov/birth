from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.models.entities import TxType, UserProfile
from app.utils.date_utils import to_occurred_date

DEFAULT_EXPENSE_CATEGORIES = ["еда", "транспорт", "дом", "здоровье", "развлечения", "прочее"]
DEFAULT_INCOME_CATEGORIES = ["зарплата", "подработка", "фриланс", "подарок", "прочее"]


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
                    occurred_at_utc TEXT,
                    occurred_date TEXT,
                    comment TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self._migrate_transactions(conn)

    def _migrate_transactions(self, conn: sqlite3.Connection) -> None:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(transactions)")}
        if "occurred_at_utc" not in cols:
            conn.execute("ALTER TABLE transactions ADD COLUMN occurred_at_utc TEXT")
        if "occurred_date" not in cols:
            conn.execute("ALTER TABLE transactions ADD COLUMN occurred_date TEXT")

        source_col = "happened_at" if "happened_at" in cols else "created_at"
        rows = conn.execute(
            f"SELECT id, occurred_at_utc, occurred_date, {source_col} as source_dt, created_at FROM transactions"
        ).fetchall()
        for row in rows:
            occ_utc = row["occurred_at_utc"]
            occ_date = row["occurred_date"]
            source = occ_utc or row["source_dt"] or row["created_at"]
            if not source:
                source = datetime.utcnow().isoformat()
            dt = datetime.fromisoformat(source)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            if not occ_utc:
                occ_utc = dt.astimezone(ZoneInfo("UTC")).isoformat()
            if not occ_date:
                occ_date = to_occurred_date(dt).isoformat()
            conn.execute(
                "UPDATE transactions SET occurred_at_utc = ?, occurred_date = ? WHERE id = ?",
                (occ_utc, occ_date, row["id"]),
            )

    def ensure_profile(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR IGNORE INTO profile(user_id) VALUES(?)", (user_id,))
        self._seed_categories()

    def _seed_categories(self) -> None:
        for name in DEFAULT_EXPENSE_CATEGORIES:
            self.add_category(name, TxType.EXPENSE)
        for name in DEFAULT_INCOME_CATEGORIES:
            self.add_category(name, TxType.INCOME)

    def get_profile(self, user_id: int) -> UserProfile:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM profile WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            self.ensure_profile(user_id)
            return self.get_profile(user_id)
        return UserProfile(
            user_id=row["user_id"],
            currency=row["currency"],
            premium_until=datetime.fromisoformat(row["premium_until"]) if row["premium_until"] else None,
            notifications_enabled=bool(row["notifications_enabled"]),
        )

    def set_notifications_enabled(self, user_id: int, enabled: bool) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE profile SET notifications_enabled = ? WHERE user_id = ?", (int(enabled), user_id))

    def set_premium_until(self, user_id: int, premium_until: datetime) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE profile SET premium_until = ? WHERE user_id = ?", (premium_until.isoformat(), user_id))

    def add_category(self, name: str, tx_type: TxType) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO categories(name, type) VALUES(?, ?)",
                (name.strip().lower(), tx_type.value),
            )

    def list_categories(self, tx_type: TxType) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT name FROM categories WHERE type = ? ORDER BY name ASC",
                (tx_type.value,),
            ).fetchall()
        return [str(r["name"]) for r in rows]

    def add_transaction(
        self,
        amount: float,
        category: str,
        tx_type: TxType,
        occurred_at_utc: datetime,
        comment: str | None = None,
    ) -> int:
        occurred_date = to_occurred_date(occurred_at_utc)
        self.add_category(category, tx_type)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO transactions(amount, category, type, occurred_at_utc, occurred_date, comment)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    amount,
                    category.strip().lower(),
                    tx_type.value,
                    occurred_at_utc.isoformat(),
                    occurred_date.isoformat(),
                    comment,
                ),
            )
            return int(cursor.lastrowid)

    def delete_transaction(self, tx_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))

    def get_last_transaction(self) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 1").fetchone()

    def month_tx_count(self, year: int, month: int) -> int:
        start = date(year, month, 1)
        end = date(year + (month // 12), (month % 12) + 1, 1)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM transactions WHERE occurred_date >= ? AND occurred_date < ?",
                (start.isoformat(), end.isoformat()),
            ).fetchone()
        return int(row["cnt"])

    def get_transactions_by_date_range(self, start: date, end: date) -> list[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, amount, category, type, occurred_at_utc, occurred_date, comment
                FROM transactions
                WHERE occurred_date >= ? AND occurred_date <= ?
                ORDER BY occurred_date DESC, id DESC
                """,
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return list(rows)

    def has_transactions_on_date(self, check_date: date) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM transactions WHERE occurred_date = ? LIMIT 1",
                (check_date.isoformat(),),
            ).fetchone()
        return bool(row)
