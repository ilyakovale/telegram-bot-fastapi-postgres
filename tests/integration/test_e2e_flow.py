from unittest.mock import AsyncMock, patch

import pytest
from account_service.__main__ import fapp as account_app
from account_service.models import Account
from handlers.account import (
    AccountStates,
    account_panel,
    handle_account_input,
    handle_address_input,
    handle_confirmation_account,
    handle_name_input,
    handle_phone_input,
)
from handlers.admin import (
    AdminStates,
    admin_panel,
    ask_delete_order_service,
    delete_order_service,
    get_all_accounts_service,
    get_all_orders_service,
)
from handlers.main import start
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
from httpx import ASGITransport, AsyncClient
from order_service.__main__ import fapp as order_app
from order_service.models import Order, Product

from tests.conftest import get_last_message, get_sent_texts


@pytest.mark.asyncio
async def test_api_e2e_flow():
    mock_acc = Account(
        chat_id=777,
        name="Ковалев Илья Сергеевич",
        address="Минск, ул. Ленина, 1",
        phone_number="+375291234567",
        block=False,
    )
    mock_prod = Product(
        id=1,
        name="Свежее молоко 1л",
        unit="шт",
        is_active=True,
        available_dates=["2026-12-31"],
    )
    mock_order = Order(
        id=55,
        chat_id=777,
        date="2026-12-31",
        last_date_before_registration="2026-12-25",
        products_max=[{"name": "Свежее молоко 1л", "quantity": 2}],
        products_current=[{"name": "Свежее молоко 1л", "quantity": 2}],
    )

    with (
        patch("account_service.__main__.set_account", AsyncMock()),
        patch(
            "account_service.__main__.get_account",
            AsyncMock(return_value=mock_acc),
        ),
        patch("account_service.__main__.check_account", AsyncMock(return_value=True)),
        patch(
            "account_service.__main__.get_all_accounts",
            AsyncMock(return_value=[mock_acc]),
        ),
        patch("account_service.__main__.block_account", AsyncMock(return_value=True)),
        patch(
            "account_service.__main__.unblock_account",
            AsyncMock(return_value=True),
        ),
        patch(
            "order_service.__main__.get_available_products",
            AsyncMock(return_value=[mock_prod]),
        ),
        patch(
            "order_service.__main__.create_order",
            AsyncMock(return_value=mock_order),
        ),
        patch(
            "order_service.__main__.get_orders_by_chat_id",
            AsyncMock(return_value=[mock_order]),
        ),
        patch(
            "order_service.__main__.get_all_orders",
            AsyncMock(return_value=[mock_order]),
        ),
        patch(
            "order_service.__main__.delete_order_by_id",
            AsyncMock(return_value=True),
        ),
    ):
        async with (
            AsyncClient(
                transport=ASGITransport(app=account_app),
                base_url="http://account-service",
            ) as acc_client,
            AsyncClient(
                transport=ASGITransport(app=order_app),
                base_url="http://order-service",
            ) as ord_client,
        ):
            resp_reg = await acc_client.post(
                "/account_set",
                json={
                    "chat_id": 777,
                    "command": "input_info",
                    "name": "Ковалев Илья Сергеевич",
                    "address": "Минск, ул. Ленина, 1",
                    "phone_number": "+375291234567",
                },
            )
            assert resp_reg.status_code == 200
            assert resp_reg.json()["status"] == "Данные записаны"

            resp_check = await acc_client.post("/account_check", json={"chat_id": 777})
            assert resp_check.status_code == 200
            assert resp_check.json()["exists"] is True

            resp_acc = await acc_client.post(
                "/account_get", json={"chat_id": 777, "command": "get_info"}
            )
            assert resp_acc.status_code == 200
            acc_data = resp_acc.json()
            assert acc_data["name"] == "Ковалев Илья Сергеевич"

            resp_products = await ord_client.post(
                "/products_get", json={"order_date": "31.12.2026"}
            )
            assert resp_products.status_code == 200
            products_list = resp_products.json()["products"]
            assert len(products_list) == 1
            assert products_list[0]["name"] == "Свежее молоко 1л"

            resp_order = await ord_client.post(
                "/order_create",
                json={
                    "chat_id": 777,
                    "date": "2026-12-31",
                    "last_date_before_registration": "2026-12-25",
                    "products_max": [{"name": "Свежее молоко 1л", "quantity": 2}],
                    "products_current": [{"name": "Свежее молоко 1л", "quantity": 2}],
                },
            )
            assert resp_order.status_code == 200
            assert resp_order.json()["status"] == "success"
            assert resp_order.json()["id"] == 55

            resp_my_orders = await ord_client.post("/orders_get", json={"chat_id": 777})
            assert resp_my_orders.status_code == 200
            my_orders = resp_my_orders.json()["orders"]
            assert len(my_orders) == 1
            assert my_orders[0]["id"] == 55

            resp_all_orders = await ord_client.post("/all_orders_get")
            assert resp_all_orders.status_code == 200
            all_orders = resp_all_orders.json()["orders"]
            assert len(all_orders) == 1

            resp_all_accs = await acc_client.post("/all_accounts_get")
            assert resp_all_accs.status_code == 200
            all_accs = resp_all_accs.json()["accounts"]
            assert len(all_accs) == 1

            resp_del = await ord_client.post("/order_delete", json={"order_id": 55})
            assert resp_del.status_code == 200
            assert resp_del.json()["status"] == "success"

            resp_block = await acc_client.post("/account_block", json={"chat_id": 777})
            assert resp_block.status_code == 200
            assert resp_block.json()["exists"] is True

            resp_unblock = await acc_client.post(
                "/account_unblock", json={"chat_id": 777}
            )
            assert resp_unblock.status_code == 200
            assert resp_unblock.json()["exists"] is True


@pytest.mark.asyncio
async def test_bot_conversational_e2e_flow(
    message_factory, fsm_context_factory, mock_bot, mock_api
):
    user_id = 888

    msg_start = message_factory(text="/start", user_id=user_id)
    await start(msg_start)
    assert any("Выберите пункт меню:" in t for t in get_sent_texts(mock_bot))

    msg_acc_panel = message_factory(text="ℹ️ Аккаунт", user_id=user_id)
    await account_panel(msg_acc_panel)
    last_msg = get_last_message(mock_bot)
    assert last_msg.text == "Аккаунт:"

    state_acc = fsm_context_factory(user_id=user_id)
    msg_edit = message_factory(text="Изменить данные аккаунта", user_id=user_id)
    await handle_account_input(msg_edit, state_acc)
    assert await state_acc.get_state() == AccountStates.waiting_for_name.state

    msg_fio = message_factory(text="Сидоров Сидор Сидорович", user_id=user_id)
    await handle_name_input(msg_fio, state_acc)
    assert await state_acc.get_state() == AccountStates.waiting_for_address.state

    msg_addr = message_factory(text="Брест, Московская, 10", user_id=user_id)
    await handle_address_input(msg_addr, state_acc)
    assert await state_acc.get_state() == AccountStates.waiting_for_phone.state

    msg_phone = message_factory(text="+375298889900", user_id=user_id)
    await handle_phone_input(msg_phone, state_acc)
    assert await state_acc.get_state() == AccountStates.waiting_for_confirmation.state

    mock_api.post("http://account_service:8001/account_set").respond(
        json={"status": "Данные записаны"}
    )
    msg_confirm_acc = message_factory(text="Да", user_id=user_id)
    await handle_confirmation_account(msg_confirm_acc, state_acc)
    assert await state_acc.get_state() is None

    msg_ord_panel = message_factory(text="📦 Заказать", user_id=user_id)
    await order_panel(msg_ord_panel)

    mock_api.post("http://account_service:8001/account_check").respond(
        json={"exists": True}
    )
    state_ord = fsm_context_factory(user_id=user_id)
    msg_new_ord = message_factory(text="Сделать новый заказ", user_id=user_id)
    await handle_order_start(msg_new_ord, state_ord)
    assert await state_ord.get_state() == NewOrderStates.waiting_for_date.state

    msg_date = message_factory(text="31.12.2026", user_id=user_id)
    await handle_order_date(msg_date, state_ord)
    assert await state_ord.get_state() == NewOrderStates.waiting_for_last_date.state

    mock_api.post("http://order_service:8002/products_get").respond(
        json={
            "status": "success",
            "products": [
                {"id": 1, "name": "Молоко 1л"},
                {"id": 2, "name": "Творог 200г"},
            ],
        }
    )
    msg_last_date = message_factory(text="25.12.2026", user_id=user_id)
    await handle_order_last_date(msg_last_date, state_ord)
    assert (
        await state_ord.get_state() == NewOrderStates.waiting_for_product_choice.state
    )

    msg_choose_milk = message_factory(text="Молоко 1л", user_id=user_id)
    await handle_product_choice(msg_choose_milk, state_ord)
    assert await state_ord.get_state() == NewOrderStates.waiting_for_quantity.state

    msg_qty = message_factory(text="3", user_id=user_id)
    await handle_quantity_input(msg_qty, state_ord)
    assert (
        await state_ord.get_state() == NewOrderStates.waiting_for_product_choice.state
    )

    msg_done = message_factory(text="✅ Закончить выбор", user_id=user_id)
    await handle_product_choice(msg_done, state_ord)
    assert await state_ord.get_state() == NewOrderStates.waiting_for_confirmation.state

    mock_api.post("http://order_service:8002/order_create").respond(
        json={"status": "success", "id": 101}
    )
    msg_confirm_ord = message_factory(text="Подтвердить заказ", user_id=user_id)
    await handle_confirmation_order(msg_confirm_ord, state_ord)
    assert await state_ord.get_state() is None
    assert any("Заказ успешно оформлен!" in t for t in get_sent_texts(mock_bot))

    mock_api.post("http://order_service:8002/orders_get").respond(
        json={
            "status": "success",
            "orders": [
                {
                    "id": 101,
                    "date": "2026-12-31",
                    "products_current": [{"name": "Молоко 1л", "quantity": 3}],
                }
            ],
        }
    )
    msg_view_orders = message_factory(text="Посмотреть свои заказы", user_id=user_id)
    await handle_view_my_orders(msg_view_orders)
    assert any("Заказ #101" in t for t in get_sent_texts(mock_bot))

    admin_id = 2112582980
    msg_admin_panel = message_factory(
        text="Панель администратора", user_id=admin_id, is_admin=True
    )
    await admin_panel(msg_admin_panel)
    assert any("Панель администратора:" in t for t in get_sent_texts(mock_bot))

    mock_api.post("http://account_service:8001/all_accounts_get").respond(
        json={
            "status": "success",
            "accounts": [
                {
                    "chat_id": user_id,
                    "name": "Сидоров Сидор Сидорович",
                    "address": "Брест",
                    "phone_number": "+375298889900",
                    "block": False,
                }
            ],
        }
    )
    msg_admin_view_accs = message_factory(
        text="Просмотреть всех", user_id=admin_id, is_admin=True
    )
    await get_all_accounts_service(msg_admin_view_accs)
    assert any("Сидоров Сидор Сидорович" in t for t in get_sent_texts(mock_bot))

    mock_api.post("http://order_service:8002/all_orders_get").respond(
        json={
            "status": "success",
            "orders": [
                {
                    "id": 101,
                    "chat_id": user_id,
                    "date": "2026-12-31",
                    "last_date_before_registration": "2026-12-25",
                    "products_current": [{"name": "Молоко 1л", "quantity": 3}],
                }
            ],
        }
    )
    msg_admin_view_orders = message_factory(
        text="Просмотреть заказы", user_id=admin_id, is_admin=True
    )
    await get_all_orders_service(msg_admin_view_orders)
    assert any("Заказ #101" in t for t in get_sent_texts(mock_bot))

    state_admin = fsm_context_factory(user_id=admin_id)
    msg_del_req = message_factory(text="Удалить заказ", user_id=admin_id, is_admin=True)
    await ask_delete_order_service(msg_del_req, state_admin)
    assert await state_admin.get_state() == AdminStates.waiting_for_delete_order.state

    mock_api.post("http://order_service:8002/order_delete").respond(
        json={"status": "success"}
    )
    msg_del_id = message_factory(text="101", user_id=admin_id, is_admin=True)
    await delete_order_service(msg_del_id, state_admin)
    assert await state_admin.get_state() is None
    assert any("Заказ 101 успешно удален." in t for t in get_sent_texts(mock_bot))
