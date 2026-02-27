from __future__ import annotations

from pathlib import Path

from app.repositories.user_db import UserRepository


class RepositoryFactory:
    def __init__(self, user_db_dir: Path) -> None:
        self.user_db_dir = user_db_dir

    def user_repo(self, user_id: int) -> UserRepository:
        return UserRepository(self.user_db_dir / f"{user_id}.db")
