import pytest
from handlers.admin import (
    AdminStates,
    admin_account_panel,
    admin_order_panel,
    admin_panel,
    ask_block_account_service,
    ask_delete_order_service,
    ask_unblock_account_service,
    back_to_admin,
    block_account_service,
    delete_order_service,
    get_all_accounts_service,
    get_all_orders_service,
    unblock_account_service,
)

from tests.conftest import get_last_message, get_sent_texts


@pytest.mark.asyncio
async def test_admin_check_authorized_user(message_factory, mock_bot):
    msg = message_factory(text="Панель администратора", is_admin=True)
    await admin_panel(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Панель администратора:"
    buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "🔒 Управление пользователями" in buttons
    assert "📦 Управление заказами" in buttons
    assert "Назад" in buttons


@pytest.mark.asyncio
async def test_admin_check_unauthorized_user(message_factory, mock_bot):
    msg = message_factory(text="Панель администратора", user_id=999, is_admin=False)
    await admin_panel(msg)
    assert len(mock_bot.call_args_list) == 0


@pytest.mark.asyncio
async def test_admin_back_to_admin(message_factory, mock_bot):
    msg = message_factory(text="◀️ Назад", is_admin=True)
    await back_to_admin(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Панель администратора:"


@pytest.mark.asyncio
async def test_admin_account_panel(message_factory, mock_bot):
    msg = message_factory(text="🔒 Управление пользователями", is_admin=True)
    await admin_account_panel(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Управление пользователями:"
    buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Заблокировать" in buttons
    assert "Разблокировать" in buttons
    assert "Просмотреть всех" in buttons
    assert "◀️ Назад" in buttons


@pytest.mark.asyncio
async def test_admin_order_panel(message_factory, mock_bot):
    msg = message_factory(text="📦 Управление заказами", is_admin=True)
    await admin_order_panel(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Управление заказами:"
    buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Создать новый заказ" in buttons
    assert "Просмотреть заказы" in buttons
    assert "Удалить заказ" in buttons
    assert "◀️ Назад" in buttons


@pytest.mark.asyncio
async def test_block_user_initiation(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Заблокировать", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await ask_block_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_block.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите ID:" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_block_user_non_digit_id(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="abc", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_block)
    await block_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_block.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("ID должен быть числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_block_user_success(message_factory, fsm_context_factory, mock_bot, mock_api):
    mock_api.post("http://account_service:8001/account_block").respond(json={"exists": True})
    msg = message_factory(text="555", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_block)
    await block_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Пользователь 555 заблокирован." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_unblock_user_initiation(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Разблокировать", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await ask_unblock_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_unblock.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите ID:" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_unblock_user_non_digit_id(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="xyz", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_unblock)
    await unblock_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_unblock.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("ID должен быть числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_unblock_user_success(message_factory, fsm_context_factory, mock_bot, mock_api):
    mock_api.post("http://account_service:8001/account_unblock").respond(json={"exists": True})
    msg = message_factory(text="555", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_unblock)
    await unblock_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Пользователь 555 разблокирован." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_all_users(message_factory, mock_bot, mock_api):
    mock_api.post("http://account_service:8001/all_accounts_get").respond(
        json={
            "status": "success",
            "accounts": [
                {
                    "chat_id": 1001,
                    "name": "Иванов Иван",
                    "address": "ул. Советская, 1",
                    "phone_number": "+375 29 111 2233",
                    "block": False,
                }
            ],
        }
    )
    msg = message_factory(text="Просмотреть всех", is_admin=True)
    await get_all_accounts_service(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Все аккаунты:" in text for text in sent_texts)
    assert any("Иванов Иван" in text for text in sent_texts)
    assert any("+375 29 111 2233" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_all_orders_empty(message_factory, mock_bot, mock_api):
    mock_api.post("http://order_service:8002/all_orders_get").respond(json={"orders": []})
    msg = message_factory(text="Просмотреть заказы", is_admin=True)
    await get_all_orders_service(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Заказы не найдены." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_all_orders_with_data(message_factory, mock_bot, mock_api):
    mock_api.post("http://order_service:8002/all_orders_get").respond(
        json={
            "orders": [
                {
                    "id": 10,
                    "chat_id": 555,
                    "date": "2026-11-20",
                    "last_date_before_registration": "2026-11-15",
                    "products_current": [{"name": "Сыр 300г", "quantity": 1}],
                }
            ]
        }
    )
    msg = message_factory(text="Просмотреть заказы", is_admin=True)
    await get_all_orders_service(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Все заказы:" in text for text in sent_texts)
    assert any("Заказ #10:" in text for text in sent_texts)
    assert any("Пользователь: 555" in text for text in sent_texts)
    assert any("Сыр 300г: 1 шт." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_delete_order_initiation(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Удалить заказ", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await ask_delete_order_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_delete_order.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите ID заказа для удаления:" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_delete_order_non_digit_id(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="order_ten", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_delete_order)
    await delete_order_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_delete_order.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("ID заказа должен быть числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_delete_order_success(message_factory, fsm_context_factory, mock_bot, mock_api):
    mock_api.post("http://order_service:8002/order_delete").respond(json={"status": "success"})
    msg = message_factory(text="10", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_delete_order)
    await delete_order_service(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Заказ 10 успешно удален." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_unauthorized_user_blocked_from_admin_actions(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Удалить заказ", user_id=999, is_admin=False)
    state = fsm_context_factory(user_id=999)
    await ask_delete_order_service(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    assert len(mock_bot.call_args_list) == 0

    await ask_block_account_service(msg, state)
    assert await state.get_state() is None
    assert len(mock_bot.call_args_list) == 0

    await get_all_orders_service(msg)
    assert len(mock_bot.call_args_list) == 0


@pytest.mark.asyncio
async def test_delete_order_api_error_response(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    mock_api.post("http://order_service:8002/order_delete").respond(
        status_code=404, json={"message": "Заказ не найден"}
    )
    msg = message_factory(text="999", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_delete_order)
    await delete_order_service(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Ошибка удаления заказа:" in text for text in sent_texts)
    assert not any("Заказ 999 успешно удален." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_all_orders_api_error_response(message_factory, mock_bot, mock_api):
    mock_api.post("http://order_service:8002/all_orders_get").respond(status_code=500)
    msg = message_factory(text="Просмотреть заказы", is_admin=True)
    await get_all_orders_service(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Ошибка загрузки заказов:" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_block_user_non_text_message(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text=None, is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_block)
    await block_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_block.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("ID должен быть числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_unblock_user_non_text_message(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text=None, is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_unblock)
    await unblock_account_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_unblock.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("ID должен быть числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_delete_order_non_text_message(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text=None, is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_delete_order)
    await delete_order_service(msg, state)
    current_state = await state.get_state()
    assert current_state == AdminStates.waiting_for_delete_order.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("ID заказа должен быть числом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_block_user_cancel_via_back_button(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="◀️ Назад", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_block)
    await block_account_service(msg, state)
    assert await state.get_state() is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Действие отменено." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_unblock_user_cancel_via_back_button(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="◀️ Назад", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_unblock)
    await unblock_account_service(msg, state)
    assert await state.get_state() is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Действие отменено." in text for text in sent_texts)


@pytest.mark.asyncio
async def test_delete_order_cancel_via_back_button(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="◀️ Назад", is_admin=True)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AdminStates.waiting_for_delete_order)
    await delete_order_service(msg, state)
    assert await state.get_state() is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Действие отменено." in text for text in sent_texts)
