import os
import sys
import random
import logging
import asyncio
import signal
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Константы
PORT = int(os.environ.get("PORT", 8000))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def get_name(update: Update) -> str:
    """Получить имя пользователя"""
    return update.effective_user.first_name or "Пользователь"

async def send_safe(update: Update, text: str) -> None:
    """Отправить сообщение с безопасным парсингом Markdown"""
    try:
        await update.message.reply_text(text, parse_mode='Markdown')
    except BadRequest:
        # Если Markdown не проходит, отправляем без форматирования
        await update.message.reply_text(text.replace('*', ''))
    except (TimedOut, NetworkError) as e:
        logger.error(f"Ошибка отправки: {e}")
        await update.message.reply_text("⚠️ Ошибка связи, попробуйте позже")

async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /me"""
    action = ' '.join(context.args).strip()
    if not action:
        await update.message.reply_text(
            "📝 Напиши действие.\n"
            "Пример: /me покакал"
        )
        return
    
    await send_safe(update, f"*{get_name(update)}* {action}")

async def try_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /try с бросанием кубика d20"""
    args = context.args
    if not args:
        await update.message.reply_text(
            "🎲 Используй: /try <действие>\n"
            "Пример: /try заколоть всех"
        )
        return
    
    action = ' '.join(args).strip()
    roll = random.randint(1, 20)
    user = get_name(update)
    
    # Определяем результат
    if roll == 1:
        emoji, status = "💀🩸", "КРИТИЧЕСКИЙ ПРОВАЛ!"
    elif roll <= 10:
        emoji, status = "❌", "Провал."
    elif roll <= 18:
        emoji, status = "✅", "Успех."
    else:
        emoji, status = "🔥🌟", "КРИТИЧЕСКИЙ УСПЕХ!"
    
    result = f"{emoji} *{user}* {action}. {status}"
    await send_safe(update, result)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = get_name(update)
    await update.message.reply_text(
        f"👋 Привет, *{user}*!\n\n"
        "Доступные команды:\n"
        "/me <действие> - показать действие от лица пользователя\n"
        "/try <действие> - бросить d20 и проверить удачу\n"
        "/help - показать эту справку",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📖 *Справка по командам:*\n\n"
        "/me <действие> - показать действие от лица пользователя\n"
        "  Пример: /me пошел гулять\n\n"
        "/try <действие> - бросить кубик d20\n"
        "  Результаты:\n"
        "  • 1 - критический провал 💀\n"
        "  • 2-10 - провал ❌\n"
        "  • 11-18 - успех ✅\n"
        "  • 19-20 - критический успех 🔥🌟\n"
        "  Пример: /try взломать дверь\n\n"
        "/help - показать эту справку\n"
        "/start - приветствие",
        parse_mode='Markdown'
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    # Если ошибка связана с обновлением, уведомляем пользователя
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже."
            )
        except:
            pass

async def health_check(request) -> web.Response:
    """Health check для Render"""
    return web.Response(
        text="✅ Бот работает!",
        status=200
    )

async def shutdown(signal_loop, stop_event):
    """Обработчик сигналов остановки"""
    logger.info(f"Получен сигнал {signal_loop}, завершаем работу...")
    stop_event.set()

async def main() -> None:
    """Главная функция"""
    # Проверка токена
    if not TOKEN:
        logger.error("❌ ТОКЕН НЕ НАЙДЕН!")
        logger.error("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    
    # Запуск HTTP сервера для health check
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 HTTP сервер запущен на порту {PORT}")
    
    # Инициализация бота
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(CommandHandler("try", try_command))
    
    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Бот запускается...")
    
    # Настройка обработки сигналов остановки
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig, stop_event)))
        except NotImplementedError:
            # Windows не поддерживает add_signal_handler
            logger.warning(f"Сигнал {sig} не поддерживается на этой платформе")
    
    try:
        # Запуск бота с polling
        async with application:
            await application.start()
            await application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Игнорировать старые обновления
            )
            logger.info("✅ Бот успешно запущен и работает!")
            logger.info(f"📊 Статистика: {len(application.handlers)} обработчиков команд")
            
            # Ожидание сигнала остановки
            await stop_event.wait()
            
    except asyncio.CancelledError:
        logger.info("⏹️ Получен сигнал отмены")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Корректное завершение
        logger.info("🔄 Завершение работы...")
        
        try:
            await application.updater.stop()
            await application.stop()
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")
        
        try:
            await runner.cleanup()
        except Exception as e:
            logger.error(f"Ошибка при остановке HTTP сервера: {e}")
        
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Программа прервана пользователем")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)
