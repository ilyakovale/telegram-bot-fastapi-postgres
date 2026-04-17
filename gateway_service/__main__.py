import asyncio
from sqlalchemy import update
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import uvicorn
from fastapi import FastAPI, HTTPException
import threading
import httpx
from config import TOKEN, ADMINS, contacts, AccountMessageRequest

fapp = FastAPI(title="Telegram Bot Microservice")


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
         await get_account_info(update, update.effective_chat.id, "Информация об аккаунте", "HTML")
    
    elif text == "📞 Контакты":
        await update.message.reply_text(contacts)


@fapp.get("/health")
async def health_check():
    return {"status": "healthy"}

def run_fastapi():
    uvicorn.run(fapp, host="0.0.0.0", port=8000)

async def get_account_info(update: Update, chat_id: int, text: str, parse_mode: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8001/get_account",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                await update.message.reply_text(f"{result.get("message", "Данные получены")} {result.get("chat_id", "")}")
            else:
                return {"status": "error", "message": f"Ошибка: {response.status_code}"}
                
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис аккаунтов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

def main():
    global telegram_bot
    

    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()

    print("🚀 FastAPI запущен на http://localhost:8000")
    
    tapp = Application.builder().token(TOKEN).build()
    
    
    tapp.add_handler(CommandHandler("start", start))
    tapp.add_handler(CommandHandler("help", help_command))
    tapp.add_handler(CommandHandler("admin_panel", admin_panel))

    tapp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    telegram_bot= tapp.bot
    print("Бот запущен...")

    tapp.run_polling(allowed_updates=[])

if __name__ == "__main__":   
    main()


