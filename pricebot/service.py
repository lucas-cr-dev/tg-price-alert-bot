"""Command logic, independent of Telegram so it can be unit tested."""

from __future__ import annotations

from .alerts import Alert, AlertError, describe, fmt_price, normalize_symbol, parse_add_args
from .prices import PriceSource
from .storage import Store

HELP = (
    "🤖 加密货币价格提醒机器人 / Crypto price alert bot\n"
    "⚠️ 仅提醒，不交易 / Alerts only – no trading, no API keys.\n\n"
    "/add BTC above 70000 – 价格 ≥ 70000 时提醒\n"
    "/add ETH below 2000 – 价格 ≤ 2000 时提醒\n"
    "/add SOL change 5 – 相对当前价涨跌 5% 时提醒（重复）\n"
    "/list – 查看提醒\n"
    "/remove <id> – 删除提醒（/remove all 清空）\n"
    "/price BTC – 查询当前价格"
)


class Service:
    def __init__(self, store: Store, source: PriceSource) -> None:
        self.store = store
        self.source = source

    async def add(self, chat_id: int, args: list[str]) -> str:
        try:
            symbol, kind, value = parse_add_args(args)
        except AlertError as e:
            return f"❌ {e}"
        try:
            price = await self.source.get_price(symbol)
        except Exception:
            return f"❌ 找不到交易对 / unknown symbol: {symbol}"
        if kind == "above" and price >= value:
            return f"⚠️ {symbol} 当前 {fmt_price(price)} 已经 ≥ {fmt_price(value)}"
        if kind == "below" and price <= value:
            return f"⚠️ {symbol} 当前 {fmt_price(price)} 已经 ≤ {fmt_price(value)}"
        alert = Alert(None, chat_id, symbol, kind, value, ref_price=price if kind == "change" else None)
        try:
            alert = self.store.add(alert)
        except ValueError as e:
            return f"❌ {e}"
        return f"✅ #{alert.id} {describe(alert)}\n当前价格 / now: {fmt_price(price)}"

    def list(self, chat_id: int) -> str:
        alerts = self.store.list(chat_id)
        if not alerts:
            return "暂无提醒 / no alerts. 用 /add 添加。"
        return "\n".join(f"#{a.id}  {describe(a)}" for a in alerts)

    def remove(self, chat_id: int, args: list[str]) -> str:
        if len(args) != 1:
            return "❌ usage: /remove <id> | /remove all"
        if args[0].lower() == "all":
            return f"🗑 已删除 {self.store.clear(chat_id)} 条 / removed"
        try:
            alert_id = int(args[0].lstrip("#"))
        except ValueError:
            return "❌ id must be a number"
        if self.store.remove(chat_id, alert_id):
            return f"🗑 #{alert_id} 已删除 / removed"
        return f"❌ #{alert_id} 不存在 / not found"

    async def price(self, args: list[str]) -> str:
        if len(args) != 1:
            return "❌ usage: /price <symbol>"
        try:
            symbol = normalize_symbol(args[0])
            return f"💱 {symbol}: {fmt_price(await self.source.get_price(symbol))}"
        except AlertError as e:
            return f"❌ {e}"
        except Exception:
            return f"❌ 获取价格失败 / could not fetch price for {args[0]}"
