import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.client import bot
from aiogram.types import Message, Update, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx
from config import TOKEN, ADMINS, contacts

fapp = FastAPI(title="Gateway Microservice")

class AccountStates(StatesGroup):
    waiting_for_account_data = State()

async def handle_account_input(message: Message, state: FSMContext):
    text = message.text
    parts = [p.strip() for p in text.split(",")]
    
    if len(parts) != 3:
        await message.answer("Неверный формат. Введите: ФИО, Адрес, Номер телефона")
        return
    
    name, address, phone_number = parts
    
    await set_account_service(
        message,
        message.from_user.id,
        "input_info",
        name, address, phone_number
    )
    
    await state.clear()

async def handle_buttons(message: Message, state: FSMContext):
    text = message.text  
    user_id = message.from_user.id

    if user_id in ADMINS:
        if text == "📊 Статистика":
            await message.answer("Показать статистику...")

        elif text == "⚙️ Настройки":
            await message.answer("Открыть настройки...")

        elif text == "🔒 Управление пользователями":
            await message.answer("Управление пользователями...")

        elif text == "📦 Управление заказами":
            await message.answer("Управление заказами...")


    if text == "📦 Заказать":
        await message.answer("Оформляем заказ...")
    
    elif text == "ℹ️ Аккаунт":
        await account_panel(message)
    
    elif text == "📞 Контакты":
        await message.answer(contacts)

    elif text == "ℹ️ Данные аккаунта":
        await get_account_service(message, message.from_user.id, "get_info")

    elif text == "Изменить данные аккаунта":
        await message.answer("Введите данные в формате: ФИО, Адресс, Номер телефона")
        await state.set_state(AccountStates.waiting_for_account_data)

    
async def help_command(message: Message):
    await message.answer("Команды: /start, /help")

# Admin

async def admin_check(message: Message):
    user_id = message.from_user.id  
    return user_id in ADMINS


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

# Start

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
    


# Account

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
        


async def get_account_service(message: Message, chat_id: int, command: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://as:8001/account_get",
                json={
                    "chat_id": chat_id,
                    "command": command,
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                await message.answer(f"Данные аккаунта: \n ФИО : {result.get('name')} \n Адресс : {result.get('address')}\n Номер телефона : {result.get('phone_number')}")

            else:
                return {"status": "error", "message": f"Ошибка: {response.status_code}"}
                
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис аккаунтов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

async def set_account_service(message: Message, chat_id: int, command: str, name: str, address: str, phone_number: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://as:8001/account_set",
                json={
                    "chat_id": chat_id,
                    "command": command,
                    "name": name,
                    "address": address,
                    "phone_number": phone_number
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                await message.answer(result.get('status'))

            else:
                return {"status": "error", "message": f"Ошибка: {response.status_code}"}
                
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис аккаунтов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
# Order

async def order_service(message: Message,chat_id: int, command: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://os:8002/order",
                json={
                    "chat_id": chat_id,
                    "command": command,
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if (result.get('status') == "Данные отправлены"):
                    await message.answer(f"Данные аккаунта: \n ФИО : {result.get('name')} \n Адресс : {result.get('address')}\n Номер телефона : {result.get('phone_number')}")
                else:
                    await message.answer(result.get('status'))
            else:
                return {"status": "error", "message": f"Ошибка: {response.status_code}"}
                
        except httpx.TimeoutException:
            return {"status": "error", "message": "Сервис аккаунтов не отвечает"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

#__main__
global telegram_bot

async def run_fastapi():
    """Запуск FastAPI"""
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
    """Запуск aiogram3"""
    bot = Bot(token=TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.message.register(start, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(admin_panel, Command("admin_panel"))
    dp.message.register(handle_account_input, AccountStates.waiting_for_account_data)
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
