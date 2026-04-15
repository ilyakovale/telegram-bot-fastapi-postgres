import asyncio
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading

fapp = FastAPI(title="Telegram Bot Microservice")

BASE_DIR = Path(__file__).parent.parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / '.env.token')
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)
print (f"TOKEN: {TOKEN}")

ADMINS = os.getenv("ADMINS")
ADMINS = [int(admin) for admin in ADMINS.split(",")] if ADMINS else []
print (f"ADMINS: {ADMINS}")

with open(BASE_DIR / 'contacts.txt', 'r', encoding='utf-8') as file:
    contacts = file.read()
print(f"CONTACTS: {contacts}")

telegram_bot = None

class SendMessageRequest(BaseModel):
    chat_id: int  # ID чата (не объект Update)
    text: str     # Текст сообщения
    parse_mode: str = "HTML"  # Режим форматирования


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды: /start, /help")


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
    
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text  # Получаем текст нажатой кнопки
    
    if text == "📦 Заказать":
        await update.message.reply_text("Оформляем заказ...")
    
    elif text == "ℹ️ Аккаунт":
        await update.message.reply_text("Мы продаём куриную продукцию!")
    
    elif text == "📞 Контакты":
        await update.message.reply_text(contacts)

@fapp.post("/send_message")
async def api_send_message(request: SendMessageRequest):
    """Отправка сообщения через API"""
    global telegram_bot
    
    if not telegram_bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        # Используем глобальный экземпляр бота
        await telegram_bot.send_message(
            chat_id=request.chat_id,
            text=request.text,
            parse_mode=request.parse_mode
        )
        return {"status": "success", "chat_id": request.chat_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@fapp.get("/health")
async def health_check():
    return {"status": "healthy"}

def run_fastapi():
    uvicorn.run(fapp, host="0.0.0.0", port=8000)

def main():
    global telegram_bot
    
    # Запускаем FastAPI в отдельном потоке
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()
    print("🚀 FastAPI запущен на http://localhost:8000")
    
    # Запускаем бота в основном потоке
    tapp = Application.builder().token(TOKEN).build()
    telegram_bot = tapp.bot
    
    tapp.add_handler(CommandHandler("start", start))
    tapp.add_handler(CommandHandler("help", help_command))
    tapp.add_handler(CommandHandler("admin_panel", admin_panel))
    tapp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    print("🤖 Бот запущен...")
    # Это синхронный вызов, он не требует asyncio
    tapp.run_polling(allowed_updates=[])

if __name__ == "__main__":   
    main()


