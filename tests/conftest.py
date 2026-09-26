import pytest

from pricebot.prices import PriceSource
from pricebot.storage import Store


class FakeSource(PriceSource):
    name = "fake"

    def __init__(self, prices=None):
        self.prices = dict(prices or {})
        self.fail = False

    async def get_prices(self, symbols):
        if self.fail:
            raise RuntimeError("network down")
        return {s: self.prices[s] for s in symbols if s in self.prices}

    async def aclose(self):
        pass


@pytest.fixture
def store():
    s = Store(":memory:")
    yield s
    s.close()


@pytest.fixture
def source():
    return FakeSource({"BTCUSDT": 60000.0, "ETHUSDT": 3000.0})
