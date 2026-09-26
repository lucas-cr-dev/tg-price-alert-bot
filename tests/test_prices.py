import json

import httpx

from pricebot.prices import BinanceSource, GateSource


def client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_binance_batch():
    def handler(request):
        symbols = json.loads(request.url.params["symbols"])
        assert symbols == ["BTCUSDT", "ETHUSDT"]
        return httpx.Response(200, json=[{"symbol": "BTCUSDT", "price": "60000.1"},
                                         {"symbol": "ETHUSDT", "price": "3000.5"}])

    src = BinanceSource(client(handler))
    assert await src.get_prices(["ETHUSDT", "BTCUSDT"]) == {"BTCUSDT": 60000.1, "ETHUSDT": 3000.5}


async def test_binance_invalid_symbol_fallback():
    def handler(request):
        symbols = json.loads(request.url.params["symbols"])
        if "BADUSDT" in symbols:
            return httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
        return httpx.Response(200, json=[{"symbol": s, "price": "1"} for s in symbols])

    src = BinanceSource(client(handler))
    assert await src.get_prices(["BADUSDT", "BTCUSDT"]) == {"BTCUSDT": 1.0}


async def test_gate():
    def handler(request):
        assert request.url.params["currency_pair"] == "BTC_USDT"
        return httpx.Response(200, json=[{"currency_pair": "BTC_USDT", "last": "59999"}])

    src = GateSource(client(handler))
    assert await src.get_price("BTCUSDT") == 59999.0
    assert GateSource.to_pair("ETHBTC") == "ETH_BTC"
