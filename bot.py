import os
import logging
import random  # <-- ДОБАВЛЕНО
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest

# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /me <действие>.
    """
    user = update.effective_user
    user_first_name = user.first_name if user.first_name else "Пользователь"

    # Собираем действие из аргументов команды
    action = ' '.join(context.args).strip()

    if not action:
        await update.message.reply_text(
            "Пожалуйста, укажите действие после команды /me.\n"
            "Например: /me пьёт кофе"
        )
        return

    # Формируем строку: *Имя* действие
    formatted_text = f"*{user_first_name}* {action}"

    try:
        # Пробуем отправить с форматированием Markdown
        await update.message.reply_text(formatted_text, parse_mode='Markdown')
    except BadRequest as e:
        # Если в имени есть символы, ломающие Markdown, отправляем без форматирования
        logger.warning(
            "Markdown parsing failed for user '%s'. Sending plain text. Error: %s",
            user_first_name, e
        )
        plain_text = f"{user_first_name} {action}"
        await update.message.reply_text(plain_text)


# 👇 НОВАЯ ФУНКЦИЯ /try ВСТАВЛЕНА СЮДА
async def try_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /try [сложность]"""
    args = context.args
    
    # Если сложность не указана, ставим дефолт 50
    if not args:
        chance = 50
    else:
        try:
            chance = int(args[0])
            if chance < 1 or chance > 100:
                await update.message.reply_text("Сложность должна быть от 1 до 100!")
                return
        except ValueError:
            await update.message.reply_text("Напиши число после /try. Пример: /try 75")
            return

    # Кидаем кубик от 1 до 100
    roll = random.randint(1, 100)
    user = update.effective_user.first_name
    
    # Логика: 10% крит успех, 40% успех, 40% неудача, 10% крит провал
    if roll <= 10:
        result_text = f"🔥 *{user}* попытался ({chance}%). Выпало {roll}. 🌟 ПОЛНЫЙ УСПЕХ!"
    elif roll <= 50:
        result_text = f"✅ *{user}* попытался ({chance}%). Выпало {roll}. Успех!"
    elif roll <= 90:
        result_text = f"❌ *{user}* попытался ({chance}%). Выпало {roll}. Неудача..."
    else:
        result_text = f"💀 *{user}* попытался ({chance}%). Выпало {roll}.  ПОЛНЫЙ ПРОВАЛ!"
    
    try:
        await update.message.reply_text(result_text, parse_mode='Markdown')
    except BadRequest:
        await update.message.reply_text(result_text.replace('*', ''))


def main() -> None:
    """Точка входа: создаёт и запускает бота."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")
        return

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("me", me_command))
    
    # 👇 ДОБАВЛЕНА РЕГИСТРАЦИЯ НОВОЙ КОМАНДЫ /try
    application.add_handler(CommandHandler("try", try_command))

    logger.info("Бот запущен. Ожидание команд /me и /try ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
