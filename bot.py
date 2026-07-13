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


async def try_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /try [сложность] [действие]"""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "Используй: /try [сложность] <действие>\n"
            "Примеры:\n"
            "/try 75 понюхать руку\n"
            "/try украсть кошелек (по умолчанию 50%)"
        )
        return

    # Определяем сложность и начало текста действия
    chance = 50  # Дефолтное значение
    action_start_index = 0
    
    # Проверяем, является ли первое слово числом от 1 до 100
    try:
        potential_chance = int(args[0])
        if 1 <= potential_chance <= 100:
            chance = potential_chance
            action_start_index = 1  # Текст начинается со второго слова
        # Если число вне диапазона — считаем его частью текста действия
    except ValueError:
        # Первое слово не число → вся строка является действием, сложность = 50%
        pass  

    # Собираем текст действия
    action_text = ' '.join(args[action_start_index:])
    
    if not action_text.strip():
        await update.message.reply_text(f"Укажи действие! Пример: /try {chance} понюхать руку")
        return

    # Кидаем кубик
    roll = random.randint(1, 100)
    user = update.effective_user.first_name
    
    # Формируем сообщение
    base_msg = f"*{user}* попытался ({chance}%) {action_text}. Выпало {roll}."
    
    if roll <= 10:
        result_text = f" {base_msg} 🌟 ПОЛНЫЙ УСПЕХ!"
    elif roll <= 50:
        result_text = f"✅ {base_msg} Успех!"
    elif roll <= 90:
        result_text = f"❌ {base_msg} Неудача..."
    else:
        result_text = f"💀 {base_msg} 💀 ПОЛНЫЙ ПРОВАЛ!"
    
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
