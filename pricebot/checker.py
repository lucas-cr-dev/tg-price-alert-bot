"""One polling cycle: fetch prices for all active alerts and fire triggers."""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from .alerts import evaluate
from .prices import PriceSource
from .storage import Store

log = logging.getLogger(__name__)

Notify = Callable[[int, str], Awaitable[None]]


async def check_once(store: Store, source: PriceSource, notify: Notify) -> int:
    """Return number of notifications sent."""
    alerts = store.all_active()
    if not alerts:
        return 0
    try:
        prices = await source.get_prices({a.symbol for a in alerts})
    except Exception as exc:  # network hiccup: skip this cycle
        log.warning("price fetch failed: %s", exc)
        return 0
    sent = 0
    for alert in alerts:
        price = prices.get(alert.symbol)
        if price is None:
            continue
        trig = evaluate(alert, price)
        if trig is None:
            continue
        store.update(trig.alert)
        try:
            await notify(alert.chat_id, f"🔔 #{alert.id} {trig.message}")
            sent += 1
        except Exception as exc:
            log.warning("notify chat %s failed: %s", alert.chat_id, exc)
    return sent
