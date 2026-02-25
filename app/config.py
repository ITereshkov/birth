from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    bot_token: str
    openai_api_key: str | None
    consult_url: str
    admin_ids: set[int]
    data_dir: Path
    user_db_dir: Path
    users_index_path: Path


def _parse_admin_ids(raw: str | None) -> set[int]:
    if not raw:
        return set()
    result: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.add(int(part))
    return result


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN не задан")

    data_dir = Path(os.getenv("DATA_DIR", "data"))
    user_db_dir = data_dir / "users"
    user_db_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=bot_token,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        consult_url=os.getenv("CONSULT_URL", "https://example.com/consult"),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS")),
        data_dir=data_dir,
        user_db_dir=user_db_dir,
        users_index_path=data_dir / "users_index.db",
    )
