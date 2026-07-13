import os
import sys
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.error("ОШИБКА: TELEGRAM_BOT_TOKEN НЕ НАЙДЕН В ENVIRONMENT!")
        sys.exit(1)  # <-- ИСПРАВЛЕНО: теперь процесс умирает корректно

    logger.info("Запуск приложения...")
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("try", try_command))
    
    logger.info("БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == "__main__":
    main()
