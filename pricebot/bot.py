"""Telegram wiring (python-telegram-bot v21)."""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

from .checker import check_once
from .config import Settings
from .prices import make_source
from .service import HELP, Service
from .storage import Store

log = logging.getLogger(__name__)


def build_app(settings: Settings) -> Application:
    store = Store(settings.db_path)
    source = make_source(settings.price_source, settings.proxy)
    service = Service(store, source)

    builder = Application.builder().token(settings.token)
    if settings.proxy:
        builder = builder.proxy(settings.proxy).get_updates_proxy(settings.proxy)
    app = builder.build()

    user_filter = filters.User(user_id=settings.allowed_user_ids) if settings.allowed_user_ids else filters.ALL

    async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(HELP)

    async def add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(await service.add(update.effective_chat.id, ctx.args))

    async def list_(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(service.list(update.effective_chat.id))

    async def remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(service.remove(update.effective_chat.id, ctx.args))

    async def price(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(await service.price(ctx.args))

    for name, fn in [("start", start), ("help", start), ("add", add), ("list", list_),
                     ("remove", remove), ("price", price)]:
        app.add_handler(CommandHandler(name, fn, filters=user_filter))

    async def notify(chat_id: int, text: str) -> None:
        await app.bot.send_message(chat_id=chat_id, text=text)

    async def tick(ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await check_once(store, source, notify)

    async def post_init(application: Application) -> None:
        await application.bot.set_my_commands([
            BotCommand("add", "添加提醒 add alert"),
            BotCommand("list", "查看提醒 list alerts"),
            BotCommand("remove", "删除提醒 remove alert"),
            BotCommand("price", "查询价格 current price"),
            BotCommand("help", "帮助 help"),
        ])

    async def post_shutdown(application: Application) -> None:
        await source.aclose()
        store.close()

    app.post_init = post_init
    app.post_shutdown = post_shutdown
    app.job_queue.run_repeating(tick, interval=settings.check_interval, first=5)
    return app


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = Settings.from_env()
    log.info("starting bot, source=%s interval=%ss", settings.price_source, settings.check_interval)
    build_app(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":  # pragma: no cover
    main()
