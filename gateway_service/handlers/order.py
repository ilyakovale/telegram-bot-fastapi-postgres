from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from keyboards.main_menu import start_keyboard
from keyboards.order_menu import (
    order_confirmation_keyboard,
    order_panel_keyboard,
    products_keyboard,
)
from services.account_service import check_account_exists
from services.order_service import create_order, get_available_products, get_user_orders

router_order = Router()


class NewOrderStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_last_date = State()
    waiting_for_product_choice = State()
    waiting_for_quantity = State()
    waiting_for_confirmation = State()


@router_order.message(F.text == "📦 Заказать")
async def order_panel(message: Message):
    await message.answer("Раздел заказов:", reply_markup=order_panel_keyboard())


@router_order.message((F.text == "Сделать новый заказ") | (F.text == "Создать новый заказ"))
async def handle_order_start(message: Message, state: FSMContext):
    exists = await check_account_exists(message.from_user.id)
    if not exists:
        await message.answer(
            "Аккаунт не найден. Пожалуйста, сначала заполните данные в разделе 'ℹ️ Аккаунт' -> 'Изменить данные аккаунта'."
        )
        return
    await message.answer(
        "Введите дату исполнения заказа в формате ДД.ММ.ГГГГ:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(NewOrderStates.waiting_for_date)


async def handle_order_date(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    raw_date = message.text.strip()
    if raw_date in ("Отменить", "Отмена", "/cancel"):
        await state.clear()
        await message.answer("Оформление заказа отменено.", reply_markup=start_keyboard())
        from .main import start

        await start(message)
        return
    try:
        parsed_date = datetime.strptime(raw_date, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    if parsed_date < date.today():
        await message.answer(
            "Дата заказа не может быть в прошлом. Введите дату в формате ДД.ММ.ГГГГ:"
        )
        return
    await state.update_data(date=raw_date)
    await message.answer("Введите конечную дату приема заявок в формате ДД.ММ.ГГГГ:")
    await state.set_state(NewOrderStates.waiting_for_last_date)


async def handle_order_last_date(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    raw_last_date = message.text.strip()
    if raw_last_date in ("Отменить", "Отмена", "/cancel"):
        await state.clear()
        await message.answer("Оформление заказа отменено.", reply_markup=start_keyboard())
        from .main import start

        await start(message)
        return
    try:
        parsed_last_date = datetime.strptime(raw_last_date, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
        return
    if parsed_last_date < date.today():
        await message.answer(
            "Конечная дата приема заявок не может быть в прошлом. Введите дату в формате ДД.ММ.ГГГГ:"
        )
        return
    data = await state.get_data()
    order_date = datetime.strptime(data["date"], "%d.%m.%Y").date()
    if parsed_last_date > order_date:
        await message.answer(
            "Конечная дата приема заявок не может быть позже даты заказа. Введите дату ДД.ММ.ГГГГ:"
        )
        return
    products = await get_available_products(data["date"])
    await state.update_data(
        last_date=raw_last_date, selected_products={}, available_products=products
    )
    await message.answer(
        "Выберите продукцию из списка или нажмите '✅ Закончить выбор':",
        reply_markup=products_keyboard(products, {}),
    )
    await state.set_state(NewOrderStates.waiting_for_product_choice)


async def handle_product_choice(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, выберите товар из предложенного списка:")
        return
    data = await state.get_data()
    selected = data.get("selected_products", {})
    products = data.get("available_products", [])
    if message.text == "✅ Закончить выбор":
        if not selected:
            await message.answer(
                "Вы не выбрали ни одного товара. Пожалуйста, выберите хотя бы один товар:"
            )
            return
        summary_lines = [
            f"Дата исполнения: {data['date']}",
            f"Конечная дата: {data['last_date']}",
            "Выбранная продукция:",
        ]
        for name, qty in selected.items():
            summary_lines.append(f"— {name}: {qty} шт.")
        summary_text = "Проверьте заказ:\n\n" + "\n".join(summary_lines)
        await message.answer(summary_text, reply_markup=order_confirmation_keyboard())
        await state.set_state(NewOrderStates.waiting_for_confirmation)
        return
    if message.text == "Отменить":
        await state.clear()
        await message.answer("Оформление заказа отменено.", reply_markup=start_keyboard())
        from .main import start

        await start(message)
        return
    valid_names = [p.get("name", "") if isinstance(p, dict) else str(p) for p in products]
    clean_name = None
    if message.text in valid_names:
        clean_name = message.text
    else:
        for name in valid_names:
            qty = selected.get(name)
            if qty is not None and message.text == f"{name} ({qty} шт.)":
                clean_name = name
                break
        if clean_name is None and message.text.endswith(" шт.)") and " (" in message.text:
            candidate = message.text.rsplit(" (", 1)[0].strip()
            if candidate in valid_names:
                clean_name = candidate

    if not clean_name or clean_name not in valid_names:
        await message.answer("Пожалуйста, выберите товар из предложенного списка:")
        return
    await state.update_data(current_product=clean_name)
    await message.answer(
        f"Введите количество для '{clean_name}':", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(NewOrderStates.waiting_for_quantity)


async def handle_quantity_input(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Количество должно быть целым положительным числом. Попробуйте снова:")
        return
    text = message.text.strip()
    if text in ("Отменить", "Отмена", "/cancel"):
        await state.clear()
        await message.answer("Оформление заказа отменено.", reply_markup=start_keyboard())
        from .main import start

        await start(message)
        return
    if not text.isdigit() or int(text) <= 0 or int(text) > 100000:
        await message.answer("Количество должно быть целым положительным числом. Попробуйте снова:")
        return
    qty = int(text)
    data = await state.get_data()
    current_product = data["current_product"]
    selected = dict(data.get("selected_products", {}))
    selected[current_product] = qty
    products = data.get("available_products", [])
    await state.update_data(selected_products=selected)
    await message.answer(
        f"Добавлено: {current_product} — {qty} шт.\nВыберите следующий товар или завершите выбор:",
        reply_markup=products_keyboard(products, selected),
    )
    await state.set_state(NewOrderStates.waiting_for_product_choice)


async def handle_confirmation_order(message: Message, state: FSMContext):
    if message.text == "Подтвердить заказ":
        data = await state.get_data()
        order_date_iso = datetime.strptime(data["date"], "%d.%m.%Y").strftime("%Y-%m-%d")
        last_date_iso = datetime.strptime(data["last_date"], "%d.%m.%Y").strftime("%Y-%m-%d")
        products_list = [
            {"name": k, "quantity": v} for k, v in data.get("selected_products", {}).items()
        ]
        order_data = {
            "date": order_date_iso,
            "last_date_before_registration": last_date_iso,
            "products_max": products_list,
            "products_current": products_list,
        }
        result = await create_order(message.from_user.id, order_data)
        await state.clear()
        if result.get("status") == "error":
            await message.answer(
                f"Ошибка оформления заказа: {result.get('message')}",
                reply_markup=start_keyboard(),
            )
        else:
            await message.answer("Заказ успешно оформлен!", reply_markup=start_keyboard())
        from .main import start

        await start(message)
    elif message.text == "Отменить":
        await state.clear()
        await message.answer("Заказ отменен.", reply_markup=start_keyboard())
        from .main import start

        await start(message)
    else:
        await message.answer(
            "Пожалуйста, подтвердите заказ кнопкой 'Подтвердить заказ' или отмените 'Отменить':",
            reply_markup=order_confirmation_keyboard(),
        )


@router_order.message(F.text == "Посмотреть свои заказы")
async def handle_view_my_orders(message: Message):
    result = await get_user_orders(message.from_user.id)
    if isinstance(result, dict) and result.get("status") == "error":
        await message.answer(
            f"Не удалось загрузить заказы: {result.get('message', 'Ошибка сервиса')}",
            reply_markup=order_panel_keyboard(),
        )
        return
    orders = result.get("orders", []) if isinstance(result, dict) else result
    if not orders:
        await message.answer("У вас нет активных заказов.", reply_markup=order_panel_keyboard())
        return
    parts = []
    for order in orders:
        order_id = order.get("id", "—")
        order_date = order.get("date", "—")
        products = order.get("products_current", [])
        items_str = (
            ", ".join([f"{p.get('name', 'Товар')}: {p.get('quantity', 1)} шт." for p in products])
            if isinstance(products, list)
            else str(products)
        )
        parts.append(f"Заказ #{order_id} на {order_date}\nСостав: {items_str}")
    text = "📋 Ваши заказы:\n\n" + "\n\n".join(parts)
    await message.answer(text, reply_markup=order_panel_keyboard())


router_order.message.register(handle_order_date, NewOrderStates.waiting_for_date)
router_order.message.register(handle_order_last_date, NewOrderStates.waiting_for_last_date)
router_order.message.register(handle_product_choice, NewOrderStates.waiting_for_product_choice)
router_order.message.register(handle_quantity_input, NewOrderStates.waiting_for_quantity)
router_order.message.register(handle_confirmation_order, NewOrderStates.waiting_for_confirmation)
