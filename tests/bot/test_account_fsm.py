import pytest
from handlers.account import (
    AccountStates,
    account_panel,
    get_account_service,
    handle_account_input,
    handle_address_input,
    handle_confirmation_account,
    handle_name_input,
    handle_phone_input,
)
from handlers.main import start

from tests.conftest import get_last_message, get_sent_texts


@pytest.mark.asyncio
async def test_start_regular_user(message_factory, mock_bot):
    msg = message_factory(text="/start", user_id=123, is_admin=False)
    await start(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Выберите пункт меню:"
    keyboard_buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "📦 Заказать" in keyboard_buttons
    assert "ℹ️ Аккаунт" in keyboard_buttons
    assert "Панель администратора" not in keyboard_buttons


@pytest.mark.asyncio
async def test_start_admin_user(message_factory, mock_bot):
    msg = message_factory(text="/start", is_admin=True)
    await start(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Выберите пункт меню:"
    keyboard_buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Панель администратора" in keyboard_buttons


@pytest.mark.asyncio
async def test_account_panel(message_factory, mock_bot):
    msg = message_factory(text="ℹ️ Аккаунт")
    await account_panel(msg)
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert sent_msg.text == "Аккаунт:"
    keyboard_buttons = [b.text for row in sent_msg.reply_markup.keyboard for b in row]
    assert "Изменить данные аккаунта" in keyboard_buttons
    assert "ℹ️ Данные аккаунта" in keyboard_buttons


@pytest.mark.asyncio
async def test_registration_initiation(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Изменить данные аккаунта")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await handle_account_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_name.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите ФИО" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_name_validation_fails_with_one_word(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Иванов")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_name)
    await handle_name_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_name.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат. Введите ФИО" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_name_validation_fails_with_two_words(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Иван Иванов")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_name)
    await handle_name_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_name.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат. Введите ФИО" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_name_validation_fails_with_four_words(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Иванов Иван Иванович Младший")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_name)
    await handle_name_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_name.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат. Введите ФИО" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_name_validation_success_advances_to_address(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Иванов Иван Иванович")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_name)
    await handle_name_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_address.state
    data = await state.get_data()
    assert data["name"] == "Иванов Иван Иванович"
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите адрес" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_address_input_advances_to_phone(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="г. Минск, пр. Независимости, 4")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_address)
    await handle_address_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    data = await state.get_data()
    assert data["address"] == "г. Минск, пр. Независимости, 4"
    sent_texts = get_sent_texts(mock_bot)
    assert any("Введите номер телефона" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_fails_without_plus(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="375291234567")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат номера" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_fails_short_number(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="+37529")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат номера" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_fails_with_letters(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="+375abc444444")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат номера" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_success_advances_to_confirmation(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="+375441234567")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await state.update_data(name="Иванов Иван Иванович", address="ул. Ленина, д. 1")
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_confirmation.state
    data = await state.get_data()
    assert data["phone_number"] == "+375 44 123 4567"
    sent_msg = get_last_message(mock_bot)
    assert sent_msg is not None
    assert "Проверьте данные:" in sent_msg.text
    assert "Иванов Иван Иванович" in sent_msg.text
    assert "+375 44 123 4567" in sent_msg.text


@pytest.mark.asyncio
async def test_confirmation_yes_saves_account_data(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    mock_api.post("http://account_service:8001/account_set").respond(
        json={"status": "Данные сохранены"}
    )
    msg = message_factory(text="Да", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(AccountStates.waiting_for_confirmation)
    await state.update_data(
        name="Иванов Иван Иванович",
        address="ул. Ленина, д. 1",
        phone_number="+375 44 123 4567",
    )
    await handle_confirmation_account(msg, state)
    current_state = await state.get_state()
    assert current_state is None
    sent_texts = get_sent_texts(mock_bot)
    assert any("Данные сохранены" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_confirmation_no_cancels_and_restarts(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="Нет", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(AccountStates.waiting_for_confirmation)
    await state.update_data(
        name="Иванов Иван Иванович",
        address="ул. Ленина, д. 1",
        phone_number="+375 44 123 4567",
    )
    await handle_confirmation_account(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_name.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Отменено. Введите данные заново." in text for text in sent_texts)
    assert any("Введите ФИО" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_account_profile_success(message_factory, mock_bot, mock_api):
    mock_api.post("http://account_service:8001/account_get").respond(
        json={
            "status": "Данные отправлены",
            "name": "Сидоров Сидор Сидорович",
            "address": "пр. Победителей, 10",
            "phone_number": "+375 29 333 2211",
        }
    )
    msg = message_factory(text="ℹ️ Данные аккаунта", user_id=456)
    await get_account_service(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Сидоров Сидор Сидорович" in text for text in sent_texts)
    assert any("пр. Победителей, 10" in text for text in sent_texts)
    assert any("+375 29 333 2211" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_view_account_profile_not_found(message_factory, mock_bot, mock_api):
    mock_api.post("http://account_service:8001/account_get").respond(
        json={"status": "Аккаунт не найден"}
    )
    msg = message_factory(text="ℹ️ Данные аккаунта", user_id=789)
    await get_account_service(msg)
    sent_texts = get_sent_texts(mock_bot)
    assert any("Аккаунт не найден" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_fails_non_by_country_code(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="+79991234567")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат номера" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_fails_too_long(message_factory, fsm_context_factory, mock_bot):
    msg = message_factory(text="+37544123456789")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат номера" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_accepts_parentheses_and_dashes(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="+375 (29) 111-22-33")
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await state.update_data(name="Иванов Иван Иванович", address="ул. Ленина, д. 1")
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_confirmation.state
    data = await state.get_data()
    assert data["phone_number"] == "+375 29 111 2233"


@pytest.mark.asyncio
async def test_confirmation_invalid_input_prompts_yes_no(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text="Не уверен", user_id=123)
    state = fsm_context_factory(user_id=123)
    await state.set_state(AccountStates.waiting_for_confirmation)
    await state.update_data(
        name="Иванов Иван Иванович",
        address="ул. Ленина, д. 1",
        phone_number="+375 44 123 4567",
    )
    await handle_confirmation_account(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_confirmation.state
    sent_texts = get_sent_texts(mock_bot)
    assert any(
        "Пожалуйста, подтвердите данные, выбрав 'Да' или 'Нет'" in text for text in sent_texts
    )


@pytest.mark.asyncio
async def test_name_validation_fails_non_text_message(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text=None)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_name)
    await handle_name_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_name.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат. Введите ФИО" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_address_validation_fails_non_text_message(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text=None)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_address)
    await handle_address_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_address.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Пожалуйста, введите адрес текстом" in text for text in sent_texts)


@pytest.mark.asyncio
async def test_phone_validation_fails_non_text_message(
    message_factory, fsm_context_factory, mock_bot
):
    msg = message_factory(text=None)
    state = fsm_context_factory(user_id=msg.from_user.id)
    await state.set_state(AccountStates.waiting_for_phone)
    await handle_phone_input(msg, state)
    current_state = await state.get_state()
    assert current_state == AccountStates.waiting_for_phone.state
    sent_texts = get_sent_texts(mock_bot)
    assert any("Неверный формат номера" in text for text in sent_texts)
