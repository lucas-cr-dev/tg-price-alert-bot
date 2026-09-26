from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    token: str
    price_source: str = "binance"
    check_interval: int = 30
    db_path: str = "data/alerts.db"
    allowed_user_ids: set[int] = field(default_factory=set)
    proxy: str | None = None

    @classmethod
    def from_env(cls, env: dict | None = None) -> "Settings":
        env = os.environ if env is None else env
        token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or "replace-me" in token:
            raise SystemExit("TELEGRAM_BOT_TOKEN is not set (copy .env.example to .env)")
        allowed = {int(x) for x in env.get("ALLOWED_USER_IDS", "").replace(" ", "").split(",") if x}
        return cls(
            token=token,
            price_source=env.get("PRICE_SOURCE", "binance"),
            check_interval=max(5, int(env.get("CHECK_INTERVAL", 30))),
            db_path=env.get("DB_PATH", "data/alerts.db"),
            allowed_user_ids=allowed,
            proxy=env.get("HTTP_PROXY_URL") or None,
        )
