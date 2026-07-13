import os
import sys
import random
import logging
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

# Хэндлер для проверки работоспособности (Health Check) от Render
async def handle_health(request):
    return web.Response(text="Бот жив и работает через вебхуки!")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    # URL вашего приложения на Render (например, https://onrender.com)
    # Render автоматически передает его в переменную RENDER_EXTERNAL_URL
    app_url = os.environ.get("RENDER_EXTERNAL_URL") 
    port = int(os.environ.get("PORT", 8000))

    if not token:
        logger.error("ТОКЕН НЕ НАЙДЕН!")
        sys.exit(1)
        
    if not app_url:
        logger.error("RENDER_EXTERNAL_URL НЕ НАЙДЕН! Убедитесь, что бот запущен на Render.")
        sys.exit(1)

    # Инициализируем бота
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("try", try_command))
    application.add_error_handler(error_handler)

    # Создаем aiohttp приложение
    app = web.Application()
    
    # Главная страница для Render Health Check
    app.router.add_get("/", handle_health)

    # Интегрируем вебхуки telegram прямо в наше aiohttp приложение
    # Бот будет слушать секретный путь /telegram_webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="telegram_webhook",
        webhook_url=f"{app_url}/telegram_webhook",
        allowed_updates=Update.ALL_TYPES,
        secret_token="SuperSecretToken123", # Защита от левых запросов
        app=app # Передаем наше aiohttp приложение
    )

if __name__ == "__main__":
    main()
