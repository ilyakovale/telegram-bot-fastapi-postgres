from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from config import ADMINS
from keyboards.admin_menu import (
    admin_account_keyboard,
    admin_main_keyboard,
    admin_order_keyboard,
)
from services.account_service import block_account, get_all_accounts, unblock_account
from services.order_service import delete_order, get_all_orders

router_admin = Router()


class AdminStates(StatesGroup):
    waiting_for_block = State()
    waiting_for_unblock = State()
    waiting_for_delete_order = State()


async def admin_check(message: Message):
    return message.from_user.id in ADMINS


@router_admin.message(F.text == "Панель администратора")
async def admin_panel(message: Message):
    if await admin_check(message):
        await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())


@router_admin.message(F.text == "◀️ Назад")
async def back_to_admin(message: Message):
    if await admin_check(message):
        await message.answer("Панель администратора:", reply_markup=admin_main_keyboard())


@router_admin.message(F.text == "🔒 Управление пользователями")
async def admin_account_panel(message: Message):
    if await admin_check(message):
        await message.answer("Управление пользователями:", reply_markup=admin_account_keyboard())


@router_admin.message(F.text == "📦 Управление заказами")
async def admin_order_panel(message: Message):
    if await admin_check(message):
        await message.answer("Управление заказами:", reply_markup=admin_order_keyboard())


@router_admin.message(F.text == "Заблокировать")
async def ask_block_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        await message.answer("Введите ID:")
        await state.set_state(AdminStates.waiting_for_block)


async def block_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        if not message.text or not message.text.isdigit():
            await message.answer("ID должен быть числом. Попробуйте ещё раз:")
            return
        chat_id = int(message.text)
        await block_account(message, chat_id)
        await state.clear()
        await message.answer(
            f"Пользователь {chat_id} заблокирован.", reply_markup=admin_main_keyboard()
        )


@router_admin.message(F.text == "Разблокировать")
async def ask_unblock_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        await message.answer("Введите ID:")
        await state.set_state(AdminStates.waiting_for_unblock)


async def unblock_account_service(message: Message, state: FSMContext):
    if await admin_check(message):
        if not message.text or not message.text.isdigit():
            await message.answer("ID должен быть числом. Попробуйте ещё раз:")
            return
        chat_id = int(message.text)
        await unblock_account(message, chat_id)
        await state.clear()
        await message.answer(
            f"Пользователь {chat_id} разблокирован.", reply_markup=admin_main_keyboard()
        )


@router_admin.message(F.text == "Просмотреть всех")
async def get_all_accounts_service(message: Message):
    if await admin_check(message):
        await get_all_accounts(message)


@router_admin.message(F.text == "Просмотреть заказы")
async def get_all_orders_service(message: Message):
    if not await admin_check(message):
        return
    result = await get_all_orders()
    if isinstance(result, dict) and result.get("status") == "error":
        await message.answer(
            f"Ошибка загрузки заказов: {result.get('message', 'Ошибка сервиса')}",
            reply_markup=admin_order_keyboard(),
        )
        return
    orders = result.get("orders", []) if isinstance(result, dict) else result
    if not orders:
        await message.answer("Заказы не найдены.", reply_markup=admin_order_keyboard())
        return
    parts = []
    for i, o in enumerate(orders):
        oid = o.get("id", "—")
        cid = o.get("chat_id", "—")
        odate = o.get("date", "—")
        ldate = o.get("last_date_before_registration", "—")
        prods = o.get("products_current", [])
        items_str = (
            ", ".join([f"{p.get('name', 'Товар')}: {p.get('quantity', 1)} шт." for p in prods])
            if isinstance(prods, list)
            else str(prods)
        )
        parts.append(
            f"Заказ #{oid}:\n"
            f"├─ Пользователь: {cid}\n"
            f"├─ Дата исполнения: {odate}\n"
            f"├─ Дедлайн: {ldate}\n"
            f"└─ Продукция: {items_str}"
        )
    text = "📋 Все заказы:\n\n" + "\n\n".join(parts)
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            chunk = text[x : x + 4096]
            if x + 4096 >= len(text):
                await message.answer(chunk, reply_markup=admin_order_keyboard())
            else:
                await message.answer(chunk)
    else:
        await message.answer(text, reply_markup=admin_order_keyboard())


@router_admin.message(F.text == "Удалить заказ")
async def ask_delete_order_service(message: Message, state: FSMContext):
    if await admin_check(message):
        await message.answer("Введите ID заказа для удаления:")
        await state.set_state(AdminStates.waiting_for_delete_order)


async def delete_order_service(message: Message, state: FSMContext):
    if await admin_check(message):
        if not message.text or not message.text.isdigit():
            await message.answer("ID заказа должен быть числом. Попробуйте ещё раз:")
            return
        order_id = int(message.text)
        result = await delete_order(order_id)
        await state.clear()
        if result.get("status") == "error":
            await message.answer(
                f"Ошибка удаления заказа: {result.get('message', 'Неизвестная ошибка')}",
                reply_markup=admin_order_keyboard(),
            )
        else:
            await message.answer(
                f"Заказ {order_id} успешно удален.", reply_markup=admin_order_keyboard()
            )


router_admin.message.register(block_account_service, AdminStates.waiting_for_block)
router_admin.message.register(unblock_account_service, AdminStates.waiting_for_unblock)
router_admin.message.register(delete_order_service, AdminStates.waiting_for_delete_order)
