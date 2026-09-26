"""SQLite persistence for alerts."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .alerts import Alert

SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL,
    symbol     TEXT    NOT NULL,
    kind       TEXT    NOT NULL,
    target     REAL    NOT NULL,
    ref_price  REAL,
    active     INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alerts_chat ON alerts(chat_id);
"""

MAX_ALERTS_PER_CHAT = 50


class Store:
    def __init__(self, path: str | Path = ":memory:") -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    @staticmethod
    def _row(r: sqlite3.Row) -> Alert:
        return Alert(
            id=r["id"],
            chat_id=r["chat_id"],
            symbol=r["symbol"],
            kind=r["kind"],
            target=r["target"],
            ref_price=r["ref_price"],
            active=bool(r["active"]),
        )

    def add(self, alert: Alert) -> Alert:
        if self.count(alert.chat_id) >= MAX_ALERTS_PER_CHAT:
            raise ValueError(f"limit of {MAX_ALERTS_PER_CHAT} alerts reached")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO alerts(chat_id, symbol, kind, target, ref_price, active) VALUES (?,?,?,?,?,?)",
                (alert.chat_id, alert.symbol, alert.kind, alert.target, alert.ref_price, int(alert.active)),
            )
        return Alert(**{**alert.__dict__, "id": cur.lastrowid})

    def count(self, chat_id: int) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE chat_id=? AND active=1", (chat_id,)
        ).fetchone()[0]

    def list(self, chat_id: int) -> list[Alert]:
        rows = self.conn.execute(
            "SELECT * FROM alerts WHERE chat_id=? AND active=1 ORDER BY id", (chat_id,)
        ).fetchall()
        return [self._row(r) for r in rows]

    def all_active(self) -> list[Alert]:
        rows = self.conn.execute("SELECT * FROM alerts WHERE active=1 ORDER BY id").fetchall()
        return [self._row(r) for r in rows]

    def update(self, alert: Alert) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE alerts SET ref_price=?, active=? WHERE id=?",
                (alert.ref_price, int(alert.active), alert.id),
            )

    def remove(self, chat_id: int, alert_id: int) -> bool:
        with self.conn:
            cur = self.conn.execute("DELETE FROM alerts WHERE id=? AND chat_id=?", (alert_id, chat_id))
        return cur.rowcount > 0

    def clear(self, chat_id: int) -> int:
        with self.conn:
            cur = self.conn.execute("DELETE FROM alerts WHERE chat_id=?", (chat_id,))
        return cur.rowcount

    def close(self) -> None:
        self.conn.close()
