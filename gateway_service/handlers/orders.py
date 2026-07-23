from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.order_menu import order_confirmation_keyboard
from keyboards.main_menu import start_keyboard
from services.account_service import check_account_exists

class NewOrderStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_last_date = State()
    waiting_for_production = State()
    waiting_for_confirmation = State()

async def order_service(message: Message, chat_id: int):
    exists = await check_account_exists(chat_id)
    if exists:
        await message.answer("Оформляем заказ...")
        # можно сразу запустить FSM, но здесь просто заглушка
    else:
        await message.answer("Аккаунт не найден. Пожалуйста, заполните данные аккаунта перед заказом.")

async def handle_order_date_input(message: Message, state: FSMContext):
    await message.answer("Введите дату заказа:", reply_markup=ReplyKeyboardRemove())
    await message.answer("число.месяц.год")
    await state.set_state(NewOrderStates.waiting_for_date)

async def handle_order_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text.strip())
    await message.answer("Введите конечную дату:")
    await state.set_state(NewOrderStates.waiting_for_last_date)

async def handle_order_last_date_input(message: Message, state: FSMContext):
    await state.update_data(last_date=message.text.strip())
    await message.answer("Введите продукцию:")
    await state.set_state(NewOrderStates.waiting_for_poduction)

async def handle_order_produciton_input(message: Message, state: FSMContext):
    await state.update_data(production=message.text.strip())
    data = await state.get_data()
    await message.answer(
        f"Проверьте заказ:\nДата: {data['date']}\nКонец: {data['last_date']}\nПродукция: {data['production']}",
        reply_markup=order_confirmation_keyboard()
    )
    await state.set_state(NewOrderStates.waiting_for_confirmation)

async def handle_confirmation_order(message: Message, state: FSMContext):
    if message.text == "Подтвердить заказ":
        # логика оформления заказа...
        await message.answer("Заказ оформлен (заглушка).", reply_markup=start_keyboard())
        await state.clear()
        from .common import start
        await start(message)
    elif message.text == "Отменить":
        await state.clear()
        from .common import start
        await start(message)