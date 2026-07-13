import os
import sys
import random
import logging
import asyncio
import signal
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_name(update):
    return update.effective_user.first_name or "Пользователь"

async def send_safe(update, text):
    try:
        await update.message.reply_text(text, parse_mode='Markdown')
    except BadRequest:
        await update.message.reply_text(text.replace('*', ''))

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = ' '.join(context.args).strip()
    if not action:
        await update.message.reply_text("Напиши действие. Пример: /me покакал")
        return
    await send_safe(update, f"*{get_name(update)}* {action}")

async def try_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Используй: /try <действие>\nПример: /try заколоть всех")
        return
    
    action = ' '.join(args).strip()
    roll = random.randint(1, 20)
    user = get_name(update)
    
    if roll == 1:
        res = f"💀 *{user}* {action}. 🩸 КРИТИЧЕСКИЙ ПРОВАЛ!"
    elif roll <= 10:
        res = f"❌ *{user}* {action}. Провал."
    elif roll <= 18:
        res = f"✅ *{user}* {action}. Успех."
    else:
        res = f"🔥 *{user}* {action}. 🌟 КРИТИЧЕСКИЙ УСПЕХ!"
    
    await send_safe(update, res)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

async def handle_health(request):
    return web.Response(text="Бот жив и работает!")

async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("ТОКЕН НЕ НАЙДЕН!")
        sys.exit(1)

    # HTTP-сервер
    port = int(os.environ.get("PORT", 8000))
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logger.info(f"HTTP на порту {port}")

    # Бот
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("try", try_command))
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и опрашивает сервер Telegram...")

    stop_event = asyncio.Event()

# Чтобы можно было остановить бота сочетанием Ctrl+C (SIGINT) или командой kill (SIGTERM)
loop = asyncio.get_running_loop()
for sig in (signal.SIGINT, signal.SIGTERM):
    try:
        loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        # В Windows этот метод не работает — там сработает KeyboardInterrupt ниже
        pass

async with application:
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Бот запущен и работает. Нажмите Ctrl+C для остановки.")
    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        pass

    # Корректная остановка
    await application.updater.stop()
    await application.stop()
    logger.info("Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main())
