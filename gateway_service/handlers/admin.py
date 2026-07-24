from aiogram.types import Message
from aiogram import Router, F
from aiogram.filters import Command

from config import ADMINS
from keyboards.admin_menu import admin_main_keyboard, admin_account_keyboard, admin_order_keyboard
from services.account_service import get_all_accounts

router_admin = Router()

async def admin_check(message: Message):
    return message.from_user.id in ADMINS

@router_admin.message(F.text == "Панель администратора")
async def admin_panel(message: Message):
    if await admin_check(message):
        await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router_admin.message(F.text == '◀️ Назад')
async def back_to_admin(message: Message):
    if await admin_check(message):
        await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())

@router_admin.message(F.text == '🔒 Управление пользователями')
async def admin_account_panel(message: Message):
    if await admin_check(message):
        await message.answer("Управление пользователями:", reply_markup=admin_account_keyboard())

@router_admin.message(F.text == '📦 Управление заказами')
async def admin_order_panel(message: Message):
    if await admin_check(message):
        await message.answer("Управление заказами:", reply_markup=admin_order_keyboard())


@router_admin.message(F.text == 'Заблокировать')
async def block_account_service(message: Message):
    if await admin_check(message):
        pass

@router_admin.message(F.text == 'Разблокировать')
async def unblock_account_service(message: Message):
    if await admin_check(message):
        pass

@router_admin.message(F.text == 'Просмотреть всех')
async def get_all_accounts_service(message: Message):
    if await admin_check(message):
        await get_all_accounts(message)   


@router_admin.message(F.text == 'Создать новый заказ')
async def new_order_service(message: Message):
    if await admin_check(message):
            pass

@router_admin.message(F.text == 'Просмотреть заказы')
async def get_all_orders_service(message: Message):
    if await admin_check(message):
            pass

@router_admin.message(F.text == 'Удалить заказ')
async def get_all_orders_service(message: Message):
    if await admin_check(message):
            pass
