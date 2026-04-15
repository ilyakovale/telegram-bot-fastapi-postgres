import asyncio
from dotenv import load_dotenv, dotenv_values
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды: /start, /help")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Бот остановлен!")

def main():
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop_command))
    
    print("🤖 Бот запущен...")
    app.run_polling(allowed_updates=[])

if __name__ == "__main__":
    main()


