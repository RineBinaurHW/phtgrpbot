# bot.py
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest

# Включаем логирование для отслеживания работы бота
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(name)


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /me <действие>.
    Берёт имя пользователя и текст после команды, отвечает в чат
    отформатированным сообщением.
    """
    user = update.effective_user
    user_first_name = user.first_name if user.first_name else "Пользователь"

    # Собираем действие из аргументов команды
    action = ' '.join(context.args).strip()

    if not action:
        # Если действие не указано, просим ввести его
        await update.message.reply_text(
            "Пожалуйста, укажите действие после команды /me.\n"
            "Например: /me пьёт кофе"
        )
        return

    # Формируем строку: *Имя* действие (parse_mode='Markdown' даст жирное имя)
    formatted_text = f"*{user_first_name}* {action}"

    try:
        # Пробуем отправить с форматированием Markdown
        await update.message.reply_text(formatted_text, parse_mode='Markdown')
    except BadRequest as e:
        # Если в имени есть символы, ломающие Markdown (например, _ или *),
        # Telegram вернёт BadRequest. Ловим ошибку и отправляем без форматирования.
        logger.warning(
            "Markdown parsing failed for user '%s'. Sending plain text. Error: %s",
            user_first_name, e
        )
        plain_text = f"{user_first_name} {action}"
        await update.message.reply_text(plain_text)


def main() -> None:
    """Точка входа: создаёт и запускает бота."""
    # Токен берётся из переменной окружения (безопасно для хостинга)
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")
        return

    # Создаём приложение и регистрируем обработчик команды /me
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("me", me_command))

    logger.info("Бот запущен. Ожидание команд /me ...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if name == "main":
    main()