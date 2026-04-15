import asyncio
from dotenv import load_dotenv, dotenv_values
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMINS = os.getenv("ADMINS")
ADMINS = [int(admin) for admin in ADMINS.split(",")] if ADMINS else []
print (ADMINS)

if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды: /start, /help")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await admin_check(update, context):
        await update.message.reply_text("Бот остановлен!")
        context.application.stop()
        context.application.shutdown()

async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in ADMINS:
        await update.message.reply_text("Вы администратор! ✅")
        return True
    else:
        await update.message.reply_text("У вас нет прав администратора! ❌")
        return False

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await admin_check(update, context):
        keyboard = [
            [KeyboardButton("📊 Статистика"), KeyboardButton("⚙️ Настройки")],
            [KeyboardButton("🔒 Управление пользователями")],
            [KeyboardButton("📦 Управление заказами")]
        ]
        
        reply_markup1 = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        await update.message.reply_text(
            "Панель администратора:",
            reply_markup=reply_markup1
        )
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаём кнопки
    keyboard = [
        [KeyboardButton("📦 Заказать")],
        [KeyboardButton("ℹ️ Аккаунт"), KeyboardButton("📞 Контакты")],
        [KeyboardButton("📍 Адрес"), KeyboardButton("🕐 Режим работы")],
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Автоматический размер
        one_time_keyboard=False  # Не скрывать после нажатия
    )
    
    await update.message.reply_text(
        "Выберите пункт меню:",
        reply_markup=reply_markup
    )
    


def main():
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("admin_panel", admin_panel))
    print("🤖 Бот запущен...")
    app.run_polling(allowed_updates=[])

if __name__ == "__main__":   
    main()


