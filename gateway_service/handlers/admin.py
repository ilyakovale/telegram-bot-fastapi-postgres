from aiogram.types import Message
from config import ADMINS
from keyboards.admin_menu import admin_main_keyboard, admin_account_keyboard, admin_order_keyboard
from services.account_service import get_all_accounts as get_all_acc_srv

async def admin_check(message: Message):
    return message.from_user.id in ADMINS

async def admin_panel(message: Message):
    if await admin_check(message):
        await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

async def admin_account_panel(message: Message):
    if await admin_check(message):
        await message.answer("Управление пользователями:", reply_markup=admin_account_keyboard())

async def admin_order_panel(message: Message):
    if await admin_check(message):
        await message.answer("Управление заказами:", reply_markup=admin_order_keyboard())

async def get_all_accounts_service(message: Message):
    await get_all_acc_srv(message)   # вызов из services/account_service.py