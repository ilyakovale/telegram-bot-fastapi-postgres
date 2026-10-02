from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
import respx
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, User
from handlers.account import router_account
from handlers.admin import router_admin
from handlers.main import router_main
from handlers.order import router_order


def get_sent_texts(bot: AsyncMock) -> list[str]:
    texts = []
    for call in bot.call_args_list:
        if (
            call.args
            and hasattr(call.args[0], "text")
            and call.args[0].text is not None
        ):
            texts.append(call.args[0].text)
    return texts


def get_last_message(bot: AsyncMock):
    for call in reversed(bot.call_args_list):
        if call.args and hasattr(call.args[0], "text"):
            return call.args[0]
    return None


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=Bot)
    bot.id = 999999
    dummy_message = Message(
        message_id=2,
        date=datetime.now(timezone.utc),
        chat=Chat(id=123, type="private"),
        from_user=User(id=999999, is_bot=True, first_name="Bot"),
        text="",
    ).as_(bot)
    bot.return_value = dummy_message
    return bot


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def dp(storage):
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router_admin)
    dispatcher.include_router(router_account)
    dispatcher.include_router(router_order)
    dispatcher.include_router(router_main)
    return dispatcher


@pytest.fixture
def user_factory():
    def _create_user(user_id=123, is_admin=False, first_name="TestUser"):
        uid = 2112582980 if is_admin else user_id
        return User(id=uid, is_bot=False, first_name=first_name)

    return _create_user


@pytest.fixture
def message_factory(mock_bot):
    def _create_message(text="", user_id=123, chat_id=None, is_admin=False, bot=None):
        target_bot = bot or mock_bot
        uid = 2112582980 if is_admin else user_id
        cid = uid if chat_id is None else chat_id
        msg = Message(
            message_id=1,
            date=datetime.now(timezone.utc),
            chat=Chat(id=cid, type="private"),
            from_user=User(
                id=uid, is_bot=False, first_name="Admin" if is_admin else "TestUser"
            ),
            text=text,
        )
        return msg.as_(target_bot)

    return _create_message


@pytest.fixture
def fsm_context_factory(storage):
    def _create_fsm_context(user_id=123, chat_id=None, bot_id=999999):
        cid = user_id if chat_id is None else chat_id
        key = StorageKey(bot_id=bot_id, chat_id=cid, user_id=user_id)
        return FSMContext(storage=storage, key=key)

    return _create_fsm_context


@pytest.fixture
def mock_api():
    with respx.mock(assert_all_called=False) as respx_mock:
        yield respx_mock
