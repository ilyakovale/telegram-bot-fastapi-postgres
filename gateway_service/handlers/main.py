from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import Router,  F

from config import contacts, ADMINS

from keyboards.main_menu import start_admin_keyboard, start_keyboard

# Импорты функций из других handlers
from .account import account_panel, handle_account_input, get_account_service
from .order import order_service, handle_order_date_input

router_main = Router()

@router_main.message(CommandStart())
async def start(message: Message):
    if message.from_user.id in ADMINS:
        await message.answer("Выберите пункт меню:", reply_markup=start_admin_keyboard())
    else:
        await message.answer("Выберите пункт меню:", reply_markup=start_keyboard())

@router_main.message(Command('help'))
async def help_command(message: Message):
    await message.answer("Команды: /start, /help")

@router_main.message(F.text == 'Назад')
async def back_to_menu(message: Message):
    if message.from_user.id in ADMINS:
        await message.answer("Выберите пункт меню:", reply_markup=start_admin_keyboard())
    else:
        await message.answer("Выберите пункт меню:", reply_markup=start_keyboard())

@router_main.message(F.text == '📞 Контакты')
async def get_contacts(message: Message):
    await message.answer(contacts)
