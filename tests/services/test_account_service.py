from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from account_service.__main__ import fapp, lifespan
from account_service.crud import (
    _get_session,
    block_account,
    check_account,
    check_block_account,
    get_account,
    get_all_accounts,
    set_account,
    unblock_account,
)
from account_service.models import Account


class MockQueryResult:
    def __init__(self, items=None):
        self.items = items or []

    def scalars(self):
        return self

    def all(self):
        return self.items

    def scalar_one_or_none(self):
        return self.items[0] if self.items else None


class MockSession:
    def __init__(self, execute_result=None):
        self.execute_result = execute_result or MockQueryResult()
        self.added = []
        self.committed = False
        self.rolled_back = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def execute(self, statement):
        return self.execute_result


@pytest.mark.asyncio
async def test_crud_check_account_exists():
    acc = Account(
        chat_id=123,
        name="Иванов Иван",
        address="Минск",
        phone_number="+375291112233",
        block=False,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc]))
    exists = await check_account(123, session=session)
    assert exists is True


@pytest.mark.asyncio
async def test_crud_check_account_not_exists():
    session = MockSession(execute_result=MockQueryResult(items=[]))
    exists = await check_account(999, session=session)
    assert exists is False


@pytest.mark.asyncio
async def test_crud_get_account_found():
    acc = Account(
        chat_id=123,
        name="Иванов Иван",
        address="Минск",
        phone_number="+375291112233",
        block=False,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc]))
    result = await get_account(123, session=session)
    assert result is not None
    assert result.chat_id == 123
    assert result.name == "Иванов Иван"


@pytest.mark.asyncio
async def test_crud_get_account_none():
    session = MockSession(execute_result=MockQueryResult(items=[]))
    result = await get_account(999, session=session)
    assert result is None


@pytest.mark.asyncio
async def test_crud_get_all_accounts():
    acc1 = Account(
        chat_id=1,
        name="User 1",
        address="Addr 1",
        phone_number="+375291111111",
        block=False,
    )
    acc2 = Account(
        chat_id=2,
        name="User 2",
        address="Addr 2",
        phone_number="+375292222222",
        block=True,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc1, acc2]))
    all_accounts = await get_all_accounts(session=session)
    assert len(all_accounts) == 2
    assert all_accounts[0].chat_id == 1
    assert all_accounts[1].chat_id == 2


@pytest.mark.asyncio
async def test_crud_set_account_create():
    session = MockSession(execute_result=MockQueryResult(items=[]))
    acc = await set_account(
        chat_id=123,
        name="Петров Петр",
        address="Гродно",
        phone_number="+375293334455",
        session=session,
    )
    assert acc.chat_id == 123
    assert acc.name == "Петров Петр"
    assert len(session.added) == 1
    assert session.committed is True


@pytest.mark.asyncio
async def test_crud_set_account_update():
    existing = Account(
        chat_id=123,
        name="Старое Имя",
        address="Старый Адрес",
        phone_number="+375290000000",
        block=False,
    )
    session = MockSession(execute_result=MockQueryResult(items=[existing]))
    acc = await set_account(
        chat_id=123,
        name="Новое Имя",
        address="Новый Адрес",
        phone_number="+375299999999",
        session=session,
    )
    assert acc.name == "Новое Имя"
    assert acc.address == "Новый Адрес"
    assert acc.phone_number == "+375299999999"
    assert session.committed is True
    assert len(session.added) == 0


@pytest.mark.asyncio
async def test_crud_block_account_found():
    acc = Account(
        chat_id=123,
        name="User",
        address="Addr",
        phone_number="+375291112233",
        block=False,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc]))
    result = await block_account(123, session=session)
    assert result is True
    assert acc.block is True
    assert session.committed is True


@pytest.mark.asyncio
async def test_crud_block_account_not_found():
    session = MockSession(execute_result=MockQueryResult(items=[]))
    result = await block_account(999, session=session)
    assert result is False
    assert session.committed is False


@pytest.mark.asyncio
async def test_crud_unblock_account_found():
    acc = Account(
        chat_id=123,
        name="User",
        address="Addr",
        phone_number="+375291112233",
        block=True,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc]))
    result = await unblock_account(123, session=session)
    assert result is True
    assert acc.block is False
    assert session.committed is True


@pytest.mark.asyncio
async def test_crud_unblock_account_not_found():
    session = MockSession(execute_result=MockQueryResult(items=[]))
    result = await unblock_account(999, session=session)
    assert result is False
    assert session.committed is False


@pytest.mark.asyncio
async def test_crud_check_block_account_true():
    acc = Account(
        chat_id=123,
        name="User",
        address="Addr",
        phone_number="+375291112233",
        block=True,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc]))
    is_blocked = await check_block_account(123, session=session)
    assert is_blocked is True


@pytest.mark.asyncio
async def test_crud_check_block_account_false():
    acc = Account(
        chat_id=123,
        name="User",
        address="Addr",
        phone_number="+375291112233",
        block=False,
    )
    session = MockSession(execute_result=MockQueryResult(items=[acc]))
    is_blocked = await check_block_account(123, session=session)
    assert is_blocked is False


@pytest.mark.asyncio
async def test_crud_check_block_account_not_found():
    session = MockSession(execute_result=MockQueryResult(items=[]))
    is_blocked = await check_block_account(999, session=session)
    assert is_blocked is False


@pytest.mark.asyncio
async def test_crud_get_session_fallback():
    mock_session_obj = MockSession()

    @asynccontextmanager
    async def mock_async_session():
        yield mock_session_obj

    with patch("account_service.crud.async_session", mock_async_session):
        async with _get_session() as s:
            assert s is mock_session_obj


@pytest.mark.asyncio
async def test_api_health():
    async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_account_get_success():
    fake_acc = Account(
        chat_id=123,
        name="Иванов Иван",
        address="Минск",
        phone_number="+375291112233",
        block=False,
    )
    with patch("account_service.__main__.get_account", AsyncMock(return_value=fake_acc)):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/account_get", json={"chat_id": 123, "command": "get_info"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "Данные отправлены"
            assert data["name"] == "Иванов Иван"
            assert data["address"] == "Минск"
            assert data["phone_number"] == "+375291112233"


@pytest.mark.asyncio
async def test_api_account_get_not_found():
    with patch("account_service.__main__.get_account", AsyncMock(return_value=None)):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/account_get", json={"chat_id": 999, "command": "get_info"})
            assert response.status_code == 200
            assert response.json() == {"status": "Аккаунт не найден"}


@pytest.mark.asyncio
async def test_api_account_set():
    with patch("account_service.__main__.set_account", AsyncMock()) as mock_set:
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            payload = {
                "chat_id": 123,
                "command": "input_info",
                "name": "Иванов Иван",
                "address": "Минск",
                "phone_number": "+375291112233",
            }
            response = await ac.post("/account_set", json=payload)
            assert response.status_code == 200
            assert response.json() == {"status": "Данные записаны"}
            mock_set.assert_called_once_with(123, "Иванов Иван", "Минск", "+375291112233")


@pytest.mark.asyncio
async def test_api_all_accounts_get_empty():
    with patch("account_service.__main__.get_all_accounts", AsyncMock(return_value=[])):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/all_accounts_get")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["accounts"] == []


@pytest.mark.asyncio
async def test_api_all_accounts_get_with_data():
    fake_acc = Account(
        chat_id=123,
        name="Иванов Иван",
        address="Минск",
        phone_number="+375291112233",
        block=False,
    )
    with patch(
        "account_service.__main__.get_all_accounts",
        AsyncMock(return_value=[fake_acc]),
    ):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/all_accounts_get")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["accounts"]) == 1
            assert data["accounts"][0]["chat_id"] == 123
            assert data["accounts"][0]["name"] == "Иванов Иван"


@pytest.mark.asyncio
async def test_api_account_check_true():
    with patch("account_service.__main__.check_account", AsyncMock(return_value=True)):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/account_check", json={"chat_id": 123})
            assert response.status_code == 200
            assert response.json() == {"exists": True}


@pytest.mark.asyncio
async def test_api_account_check_false():
    with patch("account_service.__main__.check_account", AsyncMock(return_value=False)):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/account_check", json={"chat_id": 999})
            assert response.status_code == 200
            assert response.json() == {"exists": False}


@pytest.mark.asyncio
async def test_api_account_block():
    with patch("account_service.__main__.block_account", AsyncMock(return_value=True)):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/account_block", json={"chat_id": 123})
            assert response.status_code == 200
            assert response.json() == {"exists": True}


@pytest.mark.asyncio
async def test_api_account_unblock():
    with patch("account_service.__main__.unblock_account", AsyncMock(return_value=True)):
        async with AsyncClient(transport=ASGITransport(app=fapp), base_url="http://test") as ac:
            response = await ac.post("/account_unblock", json={"chat_id": 123})
            assert response.status_code == 200
            assert response.json() == {"exists": True}


@pytest.mark.asyncio
async def test_api_lifespan():
    mock_conn = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn

    with patch("account_service.__main__.engine", mock_engine):
        async with lifespan(fapp):
            pass
        mock_conn.run_sync.assert_called_once()


@pytest.mark.asyncio
async def test_crud_session_rollback_on_error():
    mock_session = MockSession()
    with pytest.raises(ZeroDivisionError):
        async with _get_session(mock_session):
            raise ZeroDivisionError("Forced error")
    assert mock_session.rolled_back is True
