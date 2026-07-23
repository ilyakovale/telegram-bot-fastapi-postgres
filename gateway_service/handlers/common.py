from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import contacts, ADMINS
from keyboards.main_menu import start_keyboard

# Импорты функций из других handlers
from .account import account_panel, handle_account_input, get_account_service
from .orders import order_service, handle_order_date_input
from .admin import admin_panel, admin_account_panel, admin_order_panel, get_all_accounts_service

async def start(message: Message):
    await message.answer("Выберите пункт меню:", reply_markup=start_keyboard())

async def help_command(message: Message):
    await message.answer("Команды: /start, /help")

async def handle_buttons(message: Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id

    # Админские кнопки
    if user_id in ADMINS:
        if text == "📊 Статистика":
            await message.answer("Показать статистику...")
        elif text == "⚙️ Настройки":
            await message.answer("Открыть настройки...")
        elif text == "🔒 Управление пользователями":
            await admin_account_panel(message)
        elif text == "Заблокировать":
            await message.answer("Блокировка пользователя")
        elif text == "Разблокировать":
            await message.answer("Разблокировка пользователя")
        elif text == "Просмотреть всех":
            await get_all_accounts_service(message)
        elif text == "📦 Управление заказами":
            await admin_order_panel(message)
        elif text == "Создать новый заказ":
            await handle_order_date_input(message, state)
        elif text == "Просмотреть заказы":
            await message.answer("Просматриваем заказы")
        elif text == "Удалить заказ":
            await message.answer("Удаляем заказ")
        elif text == "◀️ Назад":
            await admin_panel(message)

    # Общие кнопки
    if text == "📦 Заказать":
        await order_service(message, message.from_user.id)
    elif text == "ℹ️ Аккаунт":
        await account_panel(message)
    elif text == "Назад":
        await start(message)
    elif text == "📞 Контакты":
        await message.answer(contacts)
    elif text == "ℹ️ Данные аккаунта":
        await get_account_service(message, message.from_user.id, "get_info")
    elif text == "Изменить данные аккаунта":
        await handle_account_input(message, state)