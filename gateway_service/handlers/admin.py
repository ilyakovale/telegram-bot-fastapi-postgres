from aiogram.types import Message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from datetime import date

from config import ADMINS
from keyboards.admin_menu import admin_main_keyboard, admin_account_keyboard, admin_order_keyboard
from services.account_service import get_all_accounts, block_account, unblock_account

router_admin = Router()

class AdminStates(StatesGroup):
    waiting_for_block = State()
    waiting_for_unblock = State()

class NewOrderStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_last_date = State()
    waiting_for_stop = State()

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
async def ask_block_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        await message.answer("Введите ID:")
        await state.set_state(AdminStates.waiting_for_block)

async def block_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        if not message.text.isdigit():
            await message.answer("ID должен быть числом. Попробуйте ещё раз:")
            return
        chat_id = int(message.text)
        await block_account(message, chat_id)
        await state.clear()
        await message.answer(f"Пользователь {chat_id} заблокирован.", reply_markup=admin_main_keyboard())


router_admin.message.register(block_account_service, AdminStates.waiting_for_block)

@router_admin.message(F.text == 'Разблокировать')
async def ask_unblock_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        await message.answer("Введите ID:")
        await state.set_state(AdminStates.waiting_for_unblock)

async def unblock_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        if not message.text.isdigit():
            await message.answer("ID должен быть числом. Попробуйте ещё раз:")
            return
        chat_id = int(message.text)
        await unblock_account(message, chat_id)
        await state.clear()
        await message.answer(f"Пользователь {chat_id} разблокирован.", reply_markup=admin_main_keyboard())


router_admin.message.register(unblock_account_service, AdminStates.waiting_for_unblock)

@router_admin.message(F.text == 'Просмотреть всех')
async def get_all_accounts_service(message: Message):
    if await admin_check(message):
        await get_all_accounts(message)   


@router_admin.message(F.text == 'Создать новый заказ')
async def new_order_service(message: Message, state: FSMContext):
    if await admin_check(message):
        await message.answer("Введите дату исполнения заказа")
        await message.answer("шаблон гггг.дд.мм")
        await state.set_state(NewOrderStates.waiting_for_date)

async def read_date(message: Message, state: FSMContext):
    if await admin_check(message):
        order_date = date(message.text.split('.'))

@router_admin.message(F.text == 'Просмотреть заказы')
async def get_all_orders_service(message: Message):
    if await admin_check(message):
            pass

@router_admin.message(F.text == 'Удалить заказ')
async def get_all_orders_service(message: Message):
    if await admin_check(message):
            pass
