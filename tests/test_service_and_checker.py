from pricebot.checker import check_once
from pricebot.service import Service


async def test_add_list_remove(store, source):
    svc = Service(store, source)
    msg = await svc.add(1, ["btc", "above", "70000"])
    assert msg.startswith("✅ #1") and "60,000.00" in msg
    assert "BTCUSDT ≥ 70,000.00" in svc.list(1)
    assert "#1" in svc.remove(1, ["1"])
    assert "no alerts" in svc.list(1)


async def test_add_rejects_bad_input(store, source):
    svc = Service(store, source)
    assert (await svc.add(1, ["btc"])).startswith("❌")
    assert "unknown symbol" in await svc.add(1, ["doge", "above", "1"])
    assert "已经" in await svc.add(1, ["btc", "above", "50000"])  # already above
    assert store.list(1) == []


async def test_change_alert_stores_reference(store, source):
    svc = Service(store, source)
    await svc.add(1, ["eth", "change", "5"])
    assert store.list(1)[0].ref_price == 3000.0


async def test_remove_edge_cases(store, source):
    svc = Service(store, source)
    assert svc.remove(1, []).startswith("❌")
    assert svc.remove(1, ["abc"]).startswith("❌")
    assert "not found" in svc.remove(1, ["99"])
    await svc.add(1, ["btc", "below", "1000"])
    assert "1" in svc.remove(1, ["all"])


async def test_price(store, source):
    svc = Service(store, source)
    assert await svc.price(["BTC"]) == "💱 BTCUSDT: 60,000.00"
    assert (await svc.price(["zzz"])).startswith("❌")


async def test_checker_fires_and_persists(store, source):
    svc = Service(store, source)
    await svc.add(1, ["btc", "above", "65000"])
    await svc.add(2, ["eth", "change", "10"])
    sent = []

    async def notify(chat_id, text):
        sent.append((chat_id, text))

    assert await check_once(store, source, notify) == 0

    source.prices.update({"BTCUSDT": 65500.0, "ETHUSDT": 2600.0})
    assert await check_once(store, source, notify) == 2
    assert sent[0][0] == 1 and "65,500.00" in sent[0][1]
    assert sent[1][0] == 2 and "-13.33%" in sent[1][1]

    # above alert is now inactive, change alert re-based at 2600
    assert store.list(1) == []
    assert store.list(2)[0].ref_price == 2600.0
    assert await check_once(store, source, notify) == 0


async def test_checker_survives_network_error(store, source):
    await Service(store, source).add(1, ["btc", "above", "65000"])
    source.fail = True

    async def notify(chat_id, text):
        raise AssertionError("should not notify")

    assert await check_once(store, source, notify) == 0
