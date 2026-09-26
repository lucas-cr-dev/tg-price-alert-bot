# tg-price-alert-bot

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#) [![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-v21-2CA5E0)](https://python-telegram-bot.org) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**中文** | [English](#english)

一个 Telegram 加密货币价格提醒机器人。通过 **Binance / Gate 公开行情接口** 获取价格（无需 API Key），支持价格突破、跌破和百分比涨跌提醒，SQLite 持久化，附带 Dockerfile 和单元测试。

> ⚠️ **仅提醒，不交易。** 本项目不下单、不需要交易所 API Key、不接触任何资金。不构成投资建议。

## 功能

- `/add BTC above 70000` —— 价格 ≥ 70000 时提醒（触发一次）
- `/add ETH below 2000` —— 价格 ≤ 2000 时提醒（触发一次）
- `/add SOL change 5` —— 相对添加时价格涨/跌 5% 时提醒，触发后以新价格为基准继续监控
- `/list` 查看、`/remove <id>` 删除（`/remove all` 清空）、`/price BTC` 查询当前价
- 交易对写法宽松：`btc`、`BTCUSDT`、`eth/usdt`、`sol_usdc` 都可以
- 批量请求价格，单个无效交易对不影响其他提醒
- SQLite 存储，重启不丢失；每个会话最多 50 条提醒
- 可选白名单 `ALLOWED_USER_IDS`、可选代理 `HTTP_PROXY_URL`
- 业务逻辑与 Telegram 解耦，方便测试和二次开发

## 快速开始

1. 在 Telegram 找 [@BotFather](https://t.me/BotFather) 创建机器人，拿到 Token
2. 配置并运行：

```bash
git clone https://github.com/lucas-cr-dev/tg-price-alert-bot.git
cd tg-price-alert-bot
cp .env.example .env        # 填入 TELEGRAM_BOT_TOKEN
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pricebot
```

### Docker

```bash
cp .env.example .env        # 填入 Token
docker compose up -d --build
```

数据库保存在 `./data/alerts.db`。

## 配置（.env）

| 变量 | 说明 | 默认 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather 提供的 Token（必填） | – |
| `PRICE_SOURCE` | `binance` 或 `gate` | `binance` |
| `CHECK_INTERVAL` | 检查间隔（秒，最小 5） | `30` |
| `DB_PATH` | SQLite 路径 | `data/alerts.db` |
| `ALLOWED_USER_IDS` | 允许使用的用户 ID，逗号分隔；留空表示所有人 | 空 |
| `HTTP_PROXY_URL` | 代理（行情接口和 Telegram 共用） | 空 |

Binance 默认使用官方公开行情域名 `data-api.binance.vision`（只提供行情数据，部分地区 `api.binance.com` 会返回 451）。

## 项目结构

```
pricebot/
  alerts.py    # 纯提醒逻辑（解析、判断、格式化）
  storage.py   # SQLite
  prices.py    # Binance / Gate 公开行情
  checker.py   # 一次轮询：取价 -> 判断 -> 通知
  service.py   # 命令逻辑（与 Telegram 无关）
  bot.py       # python-telegram-bot 接线 + JobQueue 定时任务
tests/         # pytest（不联网，不需要 Token）
```

## 测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

## 关于

代码由 AI 辅助编写，并经人工审核与测试。需要定制 Telegram 机器人？欢迎在 [GitHub 主页](https://github.com/lucas-cr-dev) 联系我。

---

<a id="english"></a>
## English

A Telegram bot that sends crypto price alerts using **public Binance / Gate ticker endpoints** (no API keys). Supports price-above, price-below and percent-change alerts, SQLite persistence, a Dockerfile and unit tests.

> ⚠️ **Alerts only – no trading.** The bot never places orders, never asks for exchange API keys and never touches funds. Not financial advice.

### Commands

| Command | Meaning |
|---|---|
| `/add BTC above 70000` | notify once when price ≥ 70000 |
| `/add ETH below 2000` | notify once when price ≤ 2000 |
| `/add SOL change 5` | notify on a ±5% move from the reference price, then re-arm at the new price |
| `/list` | list active alerts |
| `/remove <id>` / `/remove all` | delete alerts |
| `/price BTC` | current price |

### Run

```bash
cp .env.example .env    # set TELEGRAM_BOT_TOKEN
pip install -r requirements.txt
python -m pricebot
# or
docker compose up -d --build
```

See the configuration table above (`PRICE_SOURCE`, `CHECK_INTERVAL`, `DB_PATH`, `ALLOWED_USER_IDS`, `HTTP_PROXY_URL`). The Binance source uses the official market-data host `data-api.binance.vision`, which also works in regions where `api.binance.com` returns HTTP 451.

### Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests cover alert logic, symbol/command parsing, SQLite storage, the polling checker and the price clients (mocked HTTP). No network or bot token needed.

### About

Code is AI-assisted and human-reviewed. Need a custom Telegram bot? Reach me via my [GitHub profile](https://github.com/lucas-cr-dev).

License: [MIT](LICENSE)
