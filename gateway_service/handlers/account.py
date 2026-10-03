from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from keyboards.account_menu import account_panel_keyboard, confirmation_keyboard
from services.account_service import get_account_info, set_account_info

router_account = Router()


class AccountStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()


@router_account.message(F.text == "ℹ️ Аккаунт")
async def account_panel(message: Message):
    await message.answer("Аккаунт:", reply_markup=account_panel_keyboard())


@router_account.message(F.text == "ℹ️ Данные аккаунта")
async def get_account_service(message: Message):
    await get_account_info(message, message.from_user.id)


@router_account.message(F.text == "Изменить данные аккаунта")
async def handle_account_input(message: Message, state: FSMContext):
    await message.answer(
        "Введите ФИО\nПример: Иванов Иван Иванович", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AccountStates.waiting_for_name)


async def handle_name_input(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Неверный формат. Введите ФИО (три слова через пробел):")
        return
    parts = [p.strip() for p in message.text.split()]
    if len(parts) != 3:
        await message.answer("Неверный формат. Введите ФИО (три слова через пробел):")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите адрес\nПример: ул. Ленина, д. 1")
    await state.set_state(AccountStates.waiting_for_address)


async def handle_address_input(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Пожалуйста, введите адрес текстом:")
        return
    await state.update_data(address=message.text.strip())
    await message.answer("Введите номер телефона\nПример: +375444444444")
    await state.set_state(AccountStates.waiting_for_phone)


async def handle_phone_input(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Неверный формат номера. Пример: +375444444444")
        return
    phone = message.text.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not phone.startswith("+375") or not phone[1:].isdigit() or len(phone) != 13:
        await message.answer("Неверный формат номера. Пример: +375444444444")
        return
    phone_formatted = phone[:4] + " " + phone[4:6] + " " + phone[6:9] + " " + phone[9:]
    await state.update_data(phone_number=phone_formatted)
    data = await state.get_data()
    await message.answer(
        f"Проверьте данные:\n"
        f"ФИО: {data['name']}\n"
        f"Адрес: {data['address']}\n"
        f"Телефон: {data['phone_number']}\n\n"
        f"Подтвердить?",
        reply_markup=confirmation_keyboard(),
    )
    await state.set_state(AccountStates.waiting_for_confirmation)


async def handle_confirmation_account(message: Message, state: FSMContext):
    if message.text == "Да":
        data = await state.get_data()
        await set_account_info(
            message,
            message.from_user.id,
            data["name"],
            data["address"],
            data["phone_number"],
        )
        await state.clear()
        from .main import start

        await start(message)
    elif message.text == "Нет":
        await message.answer("Отменено. Введите данные заново.")
        await handle_account_input(message, state)
    else:
        await message.answer(
            "Пожалуйста, подтвердите данные, выбрав 'Да' или 'Нет':",
            reply_markup=confirmation_keyboard(),
        )


router_account.message.register(handle_name_input, AccountStates.waiting_for_name)
router_account.message.register(handle_address_input, AccountStates.waiting_for_address)
router_account.message.register(handle_phone_input, AccountStates.waiting_for_phone)
router_account.message.register(handle_confirmation_account, AccountStates.waiting_for_confirmation)
