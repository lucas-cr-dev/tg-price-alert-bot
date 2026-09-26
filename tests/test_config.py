import pytest

from pricebot.bot import build_app
from pricebot.config import Settings


def test_requires_token():
    with pytest.raises(SystemExit):
        Settings.from_env({})
    with pytest.raises(SystemExit):
        Settings.from_env({"TELEGRAM_BOT_TOKEN": "123456:replace-me"})


def test_parses_env():
    s = Settings.from_env({"TELEGRAM_BOT_TOKEN": "1:abc", "ALLOWED_USER_IDS": "1, 2", "CHECK_INTERVAL": "1"})
    assert s.allowed_user_ids == {1, 2} and s.check_interval == 5


def test_build_app_registers_handlers(tmp_path):
    s = Settings(token="123:fake", db_path=str(tmp_path / "a.db"))
    app = build_app(s)
    names = {c for h in app.handlers[0] for c in h.commands}
    assert {"add", "list", "remove", "price", "help", "start"} <= names
