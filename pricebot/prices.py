"""Public ticker price sources (read-only, no API keys)."""

from __future__ import annotations

import json
import logging
from typing import Iterable

import httpx

log = logging.getLogger(__name__)


class PriceError(RuntimeError):
    pass


class PriceSource:
    name = "base"

    def __init__(self, client: httpx.AsyncClient | None = None, proxy: str | None = None) -> None:
        self.client = client or httpx.AsyncClient(timeout=10, proxy=proxy or None)

    async def get_prices(self, symbols: Iterable[str]) -> dict[str, float]:
        raise NotImplementedError

    async def get_price(self, symbol: str) -> float:
        prices = await self.get_prices([symbol])
        if symbol not in prices:
            raise PriceError(f"unknown symbol: {symbol}")
        return prices[symbol]

    async def aclose(self) -> None:
        await self.client.aclose()


class BinanceSource(PriceSource):
    """Binance public ticker.

    Defaults to the market-data-only mirror ``data-api.binance.vision``, which
    serves the same public data and is reachable in regions where
    ``api.binance.com`` answers HTTP 451.
    """

    name = "binance"
    base_url = "https://data-api.binance.vision/api/v3/ticker/price"

    async def get_prices(self, symbols: Iterable[str]) -> dict[str, float]:
        wanted = sorted(set(symbols))
        if not wanted:
            return {}
        params = {"symbols": json.dumps(wanted, separators=(",", ":"))}
        resp = await self.client.get(self.base_url, params=params)
        if resp.status_code == 400 and len(wanted) > 1:
            # one invalid symbol makes Binance reject the whole batch -> fall back per symbol
            out: dict[str, float] = {}
            for s in wanted:
                out.update(await self.get_prices([s]))
            return out
        if resp.status_code == 400:
            return {}
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            data = [data]
        return {d["symbol"]: float(d["price"]) for d in data}


class GateSource(PriceSource):
    """GET https://api.gateio.ws/api/v4/spot/tickers (public endpoint)."""

    name = "gate"
    base_url = "https://api.gateio.ws/api/v4/spot/tickers"

    @staticmethod
    def to_pair(symbol: str) -> str:
        for q in ("USDT", "USDC", "BTC", "ETH"):
            if symbol.endswith(q) and len(symbol) > len(q):
                return f"{symbol[: -len(q)]}_{q}"
        return symbol

    async def get_prices(self, symbols: Iterable[str]) -> dict[str, float]:
        out: dict[str, float] = {}
        for s in sorted(set(symbols)):
            resp = await self.client.get(self.base_url, params={"currency_pair": self.to_pair(s)})
            if resp.status_code == 400:
                continue
            resp.raise_for_status()
            data = resp.json()
            if data:
                out[s] = float(data[0]["last"])
        return out


SOURCES = {"binance": BinanceSource, "gate": GateSource}


def make_source(name: str, proxy: str | None = None) -> PriceSource:
    try:
        return SOURCES[name.lower()](proxy=proxy)
    except KeyError:
        raise ValueError(f"unknown PRICE_SOURCE {name!r}, choose from {sorted(SOURCES)}") from None
