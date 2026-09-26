import pytest

from pricebot.alerts import Alert, AlertError, describe, evaluate, fmt_price, normalize_symbol, parse_add_args


def mk(kind, target, ref=None, active=True):
    return Alert(1, 42, "BTCUSDT", kind, target, ref_price=ref, active=active)


@pytest.mark.parametrize(
    "raw,expected",
    [("btc", "BTCUSDT"), ("BTCUSDT", "BTCUSDT"), ("eth/usdt", "ETHUSDT"), ("sol_usdc", "SOLUSDC"), ("ETHBTC", "ETHBTC")],
)
def test_normalize_symbol(raw, expected):
    assert normalize_symbol(raw) == expected


@pytest.mark.parametrize("raw", ["", "b", "btc$", "x" * 20])
def test_normalize_symbol_invalid(raw):
    with pytest.raises(AlertError):
        normalize_symbol(raw)


def test_parse_add_args():
    assert parse_add_args(["btc", "above", "70,000"]) == ("BTCUSDT", "above", 70000.0)
    assert parse_add_args(["eth", "<", "2000"]) == ("ETHUSDT", "below", 2000.0)
    assert parse_add_args(["sol", "change", "5%"]) == ("SOLUSDT", "change", 5.0)


@pytest.mark.parametrize(
    "args", [[], ["btc", "above"], ["btc", "sideways", "1"], ["btc", "above", "abc"], ["btc", "above", "-5"],
             ["btc", "change", "150"]]
)
def test_parse_add_args_invalid(args):
    with pytest.raises(AlertError):
        parse_add_args(args)


def test_above_fires_once():
    a = mk("above", 100)
    assert evaluate(a, 99.99) is None
    t = evaluate(a, 100)
    assert t is not None and t.alert.active is False and "≥ 100" in t.message
    assert evaluate(t.alert, 150) is None  # deactivated


def test_below_fires():
    a = mk("below", 50)
    assert evaluate(a, 51) is None
    t = evaluate(a, 49.5)
    assert t is not None and t.alert.active is False and "📉" in t.message


def test_change_up_and_rebase():
    a = mk("change", 5, ref=100)
    assert evaluate(a, 104.9) is None
    assert evaluate(a, 95.1) is None
    t = evaluate(a, 105)
    assert t is not None and "+5.00%" in t.message
    assert t.alert.active is True and t.alert.ref_price == 105  # re-armed at new ref
    assert evaluate(t.alert, 106) is None


def test_change_down():
    t = evaluate(mk("change", 10, ref=200), 170)
    assert t is not None and "-15.00%" in t.message and "🔻" in t.message


def test_change_without_ref_or_bad_price():
    assert evaluate(mk("change", 5, ref=None), 1000) is None
    assert evaluate(mk("above", 1), 0) is None
    assert evaluate(mk("above", 1, active=False), 10) is None


def test_fmt_and_describe():
    assert fmt_price(65432.1) == "65,432.10"
    assert fmt_price(1.5) == "1.5"
    assert fmt_price(0.00001234) == "0.00001234"
    assert describe(mk("above", 70000)) == "BTCUSDT ≥ 70,000.00"
    assert describe(mk("change", 3, ref=100)) == "BTCUSDT ±3% (ref 100)"
