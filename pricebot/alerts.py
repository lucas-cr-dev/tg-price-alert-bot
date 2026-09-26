"""Pure alert logic – no I/O, fully unit tested.

Alert kinds:
    above   – fire once when price >= target
    below   – fire once when price <= target
    change  – fire when price moves +/- target % from the reference price,
              then re-arm using the new price as reference (repeating)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

KINDS = ("above", "below", "change")
SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,15}$")
QUOTES = ("USDT", "USDC", "FDUSD", "BTC", "ETH", "BNB")


class AlertError(ValueError):
    """Invalid user input."""


@dataclass(frozen=True)
class Alert:
    id: int | None
    chat_id: int
    symbol: str
    kind: str
    target: float
    ref_price: float | None = None  # used by "change" alerts
    active: bool = True


@dataclass(frozen=True)
class Trigger:
    alert: Alert  # the alert *after* evaluation (possibly deactivated / re-based)
    price: float
    message: str


def normalize_symbol(raw: str) -> str:
    """'btc' -> 'BTCUSDT', 'eth/usdt' -> 'ETHUSDT', 'BTC_USDT' -> 'BTCUSDT'."""
    s = re.sub(r"[\s/_\-]", "", raw.upper())
    if not SYMBOL_RE.match(s):
        raise AlertError(f"invalid symbol: {raw}")
    if not any(s.endswith(q) and len(s) > len(q) for q in QUOTES):
        s += "USDT"
    return s


def parse_number(raw: str) -> float:
    try:
        value = float(raw.replace(",", "").rstrip("%"))
    except ValueError:
        raise AlertError(f"not a number: {raw}") from None
    if value <= 0:
        raise AlertError("value must be positive")
    return value


def parse_add_args(args: list[str]) -> tuple[str, str, float]:
    """Parse `/add <symbol> <above|below|change> <value>`."""
    if len(args) != 3:
        raise AlertError("usage: /add <symbol> <above|below|change> <value>")
    symbol = normalize_symbol(args[0])
    kind = args[1].lower()
    aliases = {">": "above", "<": "below", "%": "change", "pct": "change"}
    kind = aliases.get(kind, kind)
    if kind not in KINDS:
        raise AlertError(f"kind must be one of: {', '.join(KINDS)}")
    value = parse_number(args[2])
    if kind == "change" and value >= 100:
        raise AlertError("percent change must be < 100")
    return symbol, kind, value


def fmt_price(p: float) -> str:
    if p >= 1000:
        return f"{p:,.2f}"
    if p >= 1:
        return f"{p:.4f}".rstrip("0").rstrip(".")
    return f"{p:.8f}".rstrip("0").rstrip(".")


def describe(alert: Alert) -> str:
    if alert.kind == "above":
        return f"{alert.symbol} ≥ {fmt_price(alert.target)}"
    if alert.kind == "below":
        return f"{alert.symbol} ≤ {fmt_price(alert.target)}"
    ref = f" (ref {fmt_price(alert.ref_price)})" if alert.ref_price else ""
    return f"{alert.symbol} ±{alert.target:g}%{ref}"


def evaluate(alert: Alert, price: float) -> Trigger | None:
    """Return a Trigger if the alert fires at `price`, else None."""
    if not alert.active or price <= 0:
        return None
    if alert.kind == "above" and price >= alert.target:
        return Trigger(
            replace(alert, active=False),
            price,
            f"📈 {alert.symbol} is {fmt_price(price)} (≥ {fmt_price(alert.target)})",
        )
    if alert.kind == "below" and price <= alert.target:
        return Trigger(
            replace(alert, active=False),
            price,
            f"📉 {alert.symbol} is {fmt_price(price)} (≤ {fmt_price(alert.target)})",
        )
    if alert.kind == "change":
        ref = alert.ref_price
        if not ref:
            return None
        pct = (price - ref) / ref * 100
        if abs(pct) >= alert.target:
            arrow = "🚀" if pct > 0 else "🔻"
            return Trigger(
                replace(alert, ref_price=price),
                price,
                f"{arrow} {alert.symbol} moved {pct:+.2f}% "
                f"({fmt_price(ref)} → {fmt_price(price)})",
            )
    return None
