import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.client import bot
from aiogram.types import Message, Update, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx
from config import TOKEN, ADMINS, contacts, AccountMessageRequest

fapp = FastAPI(title="Gateway Microservice")

async def handle_buttons(message: Message):
    text = message.text  # Получаем текст нажатой кнопки
    
    if text == "📦 Заказать":
        await message.answer("Оформляем заказ...")
    
    elif text == "ℹ️ Аккаунт":
        await account_panel(message)
    
    elif text == "📞 Контакты":
        await message.answer(contacts)

    elif text == "ℹ️ Данные аккаунта":
        await message.answer("данные")

    elif text == "Изменить данные аккаунта":
        await message.answer("Изменяем данные")

    
async def help_command(message: Message):
    await message.answer("Команды: /start, /help")

# Admin

async def admin_check(message: Message):
    user_id = message.from_user.id
    
    if user_id in ADMINS:
        await message.answer("Вы администратор! ✅")
        return True
    else:
        return False

async def admin_panel(message: Message):
    if await admin_check(message):
        keyboard = [
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🔒 Управление пользователями")],
            [KeyboardButton(text="📦 Управление заказами")]
        ]
        
        reply_markup1 = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        await message.answer(
            "Панель администратора:",
            reply_markup=reply_markup1
        )

# Start buttons

async def start(message: Message):
    # Создаём кнопки
    keyboard = [
        [KeyboardButton(text="📦 Заказать")],
        [KeyboardButton(text="ℹ️ Аккаунт"), KeyboardButton(text="📞 Контакты")],
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,  # Автоматический размер
        one_time_keyboard=False  # Не скрывать после нажатия
    )
    
    await message.answer(
        "Выберите пункт меню:",
        reply_markup=reply_markup
    )
    


# Account service

async def account_panel(message: Message):
    keyboard = [
        [KeyboardButton(text="ℹ️ Данные аккаунта")],
        [KeyboardButton(text="Изменить данные аккаунта")],
    ]
        
    reply_markup2 = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await message.answer(
        "Аккаунт:",
        reply_markup=reply_markup2
    )
        


async def get_account_info(message: Message, chat_id: int, text: str, parse_mode: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://as:8001/get_account",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                await message.answer(f"{result.get('message', 'Данные получены')} {result.get('chat_id', '')}")
            else:
                return {"status": "error", "message": f"Ошибка: {response.status_code}"}
                
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис аккаунтов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

global telegram_bot

async def run_fastapi():
    """Запуск FastAPI сервера"""
    config = uvicorn.Config(
        fapp, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=False
    )
    server = uvicorn.Server(config)
    await server.serve()

async def run_aiogram():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    dp.message.register(start, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(admin_panel, Command("admin_panel"))
    dp.message.register(handle_buttons, F.text)
    telegram_bot = bot
    await dp.start_polling(bot, allowed_updates=["message"])
    
async def main():

    print("🚀 FastAPI запущен на http://gs:8000")
    print("Бот запущен...")

    await asyncio.gather(
        run_fastapi(),
        run_aiogram()
    )



if __name__ == "__main__":   
    asyncio.run(main())


@fapp.get("/health")
async def health_check():
    return {"status": "healthy"}