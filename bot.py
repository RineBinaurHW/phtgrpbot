import os
import sys
import random
import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Обработчики команд ---
async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user.first_name else "Пользователь"
    action = ' '.join(context.args).strip()
    
    if not action:
        await update.message.reply_text("Напиши действие. Пример: /me покакал")
        return
        
    text = f"*{name}* {action}"
    try:
        await update.message.reply_text(text, parse_mode='Markdown')
    except BadRequest:
        await update.message.reply_text(text.replace('*', ''))

async def try_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Используй: /try <действие>\nПример: /try заколоть всех")
        return

    action_text = ' '.join(args).strip()
    roll = random.randint(1, 20)
    user = update.effective_user.first_name
    
    if roll == 1:
        res = f"💀 *{user}* {action_text}. 🩸 КРИТИЧЕСКИЙ ПРОВАЛ!"
    elif roll <= 10:
        res = f"❌ *{user}* {action_text}. Провал."
    elif roll <= 18:
        res = f"✅ *{user}* {action_text}. Успех."
    else:
        res = f"🔥 *{user}* {action_text}. 🌟 КРИТИЧЕСКИЙ УСПЕХ!"
    
    try:
        await update.message.reply_text(res, parse_mode='Markdown')
    except BadRequest:
        await update.message.reply_text(res.replace('*', ''))

# --- Глобальный обработчик ошибок ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Ошибка при обработке:", exc_info=context.error)

# --- Заглушка для HTTP, чтобы Render не убивал ---
async def handle_health(request):
    """Отвечает на проверки Render, возвращая 200 OK."""
    return web.Response(text="Бот жив и работает!")
    
async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("ОШИБКА: TELEGRAM_BOT_TOKEN НЕ НАЙДЕН!")
        sys.exit(1)

    # HTTP-сервер для Render
    port = int(os.environ.get("PORT", 8000))
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"HTTP-заглушка запущена на порту {port}")

    # Бот
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("try", try_command))
    application.add_error_handler(error_handler)  # ← теперь error_handler существует

    logger.info("Бот запущен и опрашивает сервер Telegram...")
    
    async with application:
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await application.updater.stop()
            await application.stop()

if __name__ == "__main__":
    asyncio.run(main())
