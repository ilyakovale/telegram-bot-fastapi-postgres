import pytest
from handlers.order import (
    NewOrderStates,
    handle_confirmation_order,
    handle_order_date,
    handle_order_last_date,
    handle_order_start,
    handle_product_choice,
    handle_quantity_input,
    handle_view_my_orders,
    order_panel,
)

from tests.conftest import get_last_message, get_sent_texts


@pytest.mark.asyncio
async def test_order_panel_menu(message_factory, mock_bot):
    msg = message_factory(text="📦 Заказать")
    await order_panel(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Раздел заказов:"
    keyboard_buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Сделать новый заказ" in keyboard_buttons
    assert "Посмотреть свои заказы" in keyboard_buttons


@pytest.mark.asyncio
async def test_order_start_account_does_not_exist(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    mock_api.post("http://account_service:8001/account_check").respond(
        json={"exists": False}
    )
    msg = message_factory(text="Сделать новый заказ", user_id=123)
    state = fsm_context_factory(user_id=123)
    await handle_order_start(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Аккаунт не найден" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_start_account_exists(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    mock_api.post("http://account_service:8001/account_check").respond(
        json={"exists": True}
    )
    msg = message_factory(text="Сделать новый заказ", user_id=123)
    state = fsm_context_factory(user_id=123)
    await handle_order_start(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_date.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите дату исполнения заказа" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_date_validation_invalid_format(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="неверная_дата", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_date)
    await handle_order_date(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_date.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат даты" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_date_validation_past_date(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="01.01.2020", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_date)
    await handle_order_date(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_date.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("не может быть в прошлом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_date_validation_valid_future_date(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="31.12.2026", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_date)
    await handle_order_date(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_last_date.state
    data = await state.get_data()
    assert data["date"] == "31.12.2026"
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите конечную дату приема заявок" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_last_date_validation_invalid_format(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="invalid_date", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_last_date)
    await state.update_data(date="31.12.2026")
    await handle_order_last_date(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_last_date.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат даты" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_last_date_after_order_date_rejected(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="15.11.2026", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_last_date)
    await state.update_data(date="10.11.2026")
    await handle_order_last_date(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_last_date.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("не может быть позже даты заказа" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_last_date_valid_shows_product_keyboard(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    mock_api.post("http://order_service:8002/products_get").respond(
        json={
            "products": [
                {"id": 1, "name": "Молоко 1л"},
                {"id": 2, "name": "Творог 200г"},
            ]
        }
    )
    msg = message_factory(text="25.12.2026", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_last_date)
    await state.update_data(date="31.12.2026")
    await handle_order_last_date(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_product_choice.state
    data = await state.get_data()
    assert data["last_date"] == "25.12.2026"
    assert "available_products" in data
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert "Выберите продукцию" in sent_msg.text
    buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Молоко 1л" in buttons
    assert "Творог 200г" in buttons
    assert "✅ Закончить выбор" in buttons


@pytest.mark.asyncio
async def test_product_choice_select_product_prompts_for_quantity(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Молоко 1л", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_product_choice)
    await state.update_data(
        available_products=[
            {"id": 1, "name": "Молоко 1л"},
            {"id": 2, "name": "Творог 200г"},
        ],
        selected_products={},
    )
    await handle_product_choice(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_quantity.state
    data = await state.get_data()
    assert data["current_product"] == "Молоко 1л"
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите количество для 'Молоко 1л'" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_product_choice_invalid_product(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Несуществующий товар", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_product_choice)
    await state.update_data(
        available_products=[{"id": 1, "name": "Молоко 1л"}], selected_products={}
    )
    await handle_product_choice(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_product_choice.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("выберите товар из предложенного списка" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_quantity_input_invalid_non_numeric(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="три", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_quantity)
    await state.update_data(
        current_product="Молоко 1л",
        available_products=[{"id": 1, "name": "Молоко 1л"}],
        selected_products={},
    )
    await handle_quantity_input(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_quantity.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("целым положительным числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_quantity_input_invalid_zero_or_negative(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="0", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_quantity)
    await state.update_data(
        current_product="Молоко 1л",
        available_products=[{"id": 1, "name": "Молоко 1л"}],
        selected_products={},
    )
    await handle_quantity_input(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_quantity.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("целым положительным числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_quantity_input_valid_records_product_and_returns_to_choice(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="4", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_quantity)
    await state.update_data(
        current_product="Молоко 1л",
        available_products=[{"id": 1, "name": "Молоко 1л"}],
        selected_products={},
    )
    await handle_quantity_input(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_product_choice.state
    data = await state.get_data()
    assert data["selected_products"] == {"Молоко 1л": 4}
    sent_texts = get_sent_texts(mock_bot)
    assert any("Добавлено: Молоко 1л — 4 шт." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_finish_choice_fails_when_no_products_selected(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="✅ Закончить выбор", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_product_choice)
    await state.update_data(
        date="31.12.2026",
        last_date="25.12.2026",
        selected_products={},
        available_products=[{"id": 1, "name": "Молоко 1л"}],
    )
    await handle_product_choice(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_product_choice.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("не выбрали ни одного товара" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_finish_choice_success_advances_to_confirmation(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="✅ Закончить выбор", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_product_choice)
    await state.update_data(
        date="31.12.2026",
        last_date="25.12.2026",
        selected_products={"Молоко 1л": 2, "Творог 200г": 1},
        available_products=[
            {"id": 1, "name": "Молоко 1л"},
            {"id": 2, "name": "Творог 200г"},
        ],
    )
    await handle_product_choice(msg, state)
    current_state = await state.get_state()
    assert current_state == NewOrderStates.waiting_for_confirmation.state
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert "Проверьте заказ:" in sent_msg.text
    assert "31.12.2026" in sent_msg.text
    assert "25.12.2026" in sent_msg.text
    assert "Молоко 1л: 2 шт." in sent_msg.text
    buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Подтвердить заказ" in buttons
    assert "Отменить" in buttons


@pytest.mark.asyncio
async def test_order_confirmation_confirm_calls_create_order_api(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    mock_api.post("http://order_service:8002/order_create").respond(
        json={"status": "success", "id": 105}
    )
    msg = message_factory(text="Подтвердить заказ", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_confirmation)
    await state.update_data(
        date="31.12.2026", last_date="25.12.2026", selected_products={"Молоко 1л": 2}
    )
    await handle_confirmation_order(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Заказ успешно оформлен!" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_confirmation_cancel(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Отменить", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_confirmation)
    await state.update_data(
        date="31.12.2026", last_date="25.12.2026", selected_products={"Молоко 1л": 2}
    )
    await handle_confirmation_order(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Заказ отменен." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_order_choice_cancel(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Отменить", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(NewOrderStates.waiting_for_product_choice)
    await handle_product_choice(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Оформление заказа отменено." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_own_orders_empty(message_factory, mock_bot, mock_api):
    mock_api.post("http://order_service:8002/orders_get").respond(json={"orders": []})
    msg = message_factory(text="Посмотреть свои заказы", user_id=123)
    await handle_view_my_orders(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("У вас нет активных заказов." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_own_orders_with_data(message_factory, mock_bot, mock_api):
    mock_api.post("http://order_service:8002/orders_get").respond(
        json={
            "orders": [
                {
                    "id": 101,
                    "date": "2026-12-31",
                    "products_current": [{"name": "Молоко 1л", "quantity": 3}],
                }
            ]
        }
    )
    msg = message_factory(text="Посмотреть свои заказы", user_id=123)
    await handle_view_my_orders(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Заказ #101 на 2026-12-31" in text for text in sent_texts)
    assert any("Молоко 1л: 3 шт." in text for text in sent_texts)
