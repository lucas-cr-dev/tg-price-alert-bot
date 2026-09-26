import pytest

from pricebot.alerts import Alert
from pricebot.storage import MAX_ALERTS_PER_CHAT, Store


def test_crud(store):
    a = store.add(Alert(None, 1, "BTCUSDT", "above", 70000))
    b = store.add(Alert(None, 1, "ETHUSDT", "change", 5, ref_price=3000))
    store.add(Alert(None, 2, "BTCUSDT", "below", 50000))
    assert a.id and b.id and a.id != b.id
    assert [x.symbol for x in store.list(1)] == ["BTCUSDT", "ETHUSDT"]
    assert len(store.all_active()) == 3

    store.update(Alert(**{**a.__dict__, "active": False}))
    assert [x.id for x in store.list(1)] == [b.id]

    assert store.remove(2, b.id) is False  # other chat can't delete it
    assert store.remove(1, b.id) is True
    assert store.list(1) == []
    assert store.clear(2) == 1


def test_persists_to_disk(tmp_path):
    path = tmp_path / "sub" / "alerts.db"
    s = Store(path)
    s.add(Alert(None, 7, "BTCUSDT", "above", 1))
    s.close()
    s2 = Store(path)
    assert s2.list(7)[0].target == 1
    s2.close()


def test_limit(store):
    for i in range(MAX_ALERTS_PER_CHAT):
        store.add(Alert(None, 1, "BTCUSDT", "above", 100000 + i))
    with pytest.raises(ValueError):
        store.add(Alert(None, 1, "BTCUSDT", "above", 1))
