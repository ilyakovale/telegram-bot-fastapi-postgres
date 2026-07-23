# app/main.py
import asyncio
import uvicorn
from fastapi import FastAPI
from aiogram import F
from aiogram.filters import Command

from dispatcher import dp, bot
from handlers.common import start, help_command, handle_buttons
from handlers.account import (
    AccountStates,
    handle_name_input,
    handle_address_input,
    handle_phone_input,
    handle_confirmation_account
)
from handlers.admin import admin_panel
from handlers.orders import (
    NewOrderStates,
    handle_order_date,
    handle_order_last_date_input,
    handle_order_produciton_input,
    handle_confirmation_order
)

# FastAPI-приложение (можно вынести в app/api/health.py, здесь оставлено для минимализма)
fapp = FastAPI(title="Gateway Microservice")

async def run_fastapi():
    """Запуск FastAPI."""
    config = uvicorn.Config(fapp, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Регистрация обработчиков команд
    dp.message.register(start, Command("start"))
    dp.message.register(help_command, Command("help"))
    dp.message.register(admin_panel, Command("admin_panel"))

    # Регистрация FSM-обработчиков аккаунта
    dp.message.register(handle_name_input, AccountStates.waiting_for_name)
    dp.message.register(handle_address_input, AccountStates.waiting_for_address)
    dp.message.register(handle_phone_input, AccountStates.waiting_for_phone)
    dp.message.register(handle_confirmation_account, AccountStates.waiting_for_confirmation)

    # Регистрация FSM-обработчиков заказов
    dp.message.register(handle_order_date, NewOrderStates.waiting_for_date)
    dp.message.register(handle_order_last_date_input, NewOrderStates.waiting_for_last_date)
    dp.message.register(handle_order_produciton_input, NewOrderStates.waiting_for_production)
    dp.message.register(handle_confirmation_order, NewOrderStates.waiting_for_confirmation)

    # Универсальный обработчик всех текстовых сообщений (кнопки главного меню, админки и пр.)
    dp.message.register(handle_buttons, F.text)

    print("🚀 FastAPI запущен на http://gateway:8000")
    print("Бот запущен...")

    # Одновременный запуск HTTP-сервера и поллинга Telegram
    await asyncio.gather(
        run_fastapi(),
        dp.start_polling(bot, allowed_updates=["message"])
    )

if __name__ == "__main__":
    asyncio.run(main())