import asyncio
from contextlib import asynccontextmanager
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import create_mock_engine

from order_service.__main__ import fapp, lifespan
from order_service.crud import (
    _get_session,
    _normalize_date,
    create_order,
    create_product,
    delete_order_by_id,
    get_all_orders,
    get_all_products,
    get_available_products,
    get_order_by_id,
    get_orders_by_chat_id,
)
from order_service.database import Base
from order_service.models import Order, Product
from order_service.schemas import (
    AvailableProductsRequest,
    OrderCreateRequest,
    OrderIDRequest,
    OrderResponse,
    OrderUserRequest,
    ProductCreateRequest,
    ProductResponse,
)


class MockQueryResult:
    def __init__(self, items=None, rowcount=0):
        self.items = items or []
        self.rowcount = rowcount

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
        self.refreshed = []
        self.rolled_back = False
        self.statements = []
        self.last_statement = None

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = 100

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, obj):
        self.refreshed.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = 100

    async def execute(self, statement):
        self.statements.append(statement)
        self.last_statement = statement
        return self.execute_result


def test_order_model_structure():
    assert Order.__tablename__ == "orders"
    columns = {col.name: col for col in Order.__table__.columns}
    assert "id" in columns
    assert "chat_id" in columns
    assert "date" in columns
    assert "last_date_before_registration" in columns
    assert "products_max" in columns
    assert "products_current" in columns
    chat_id_col = columns["chat_id"]
    assert any(
        fk.target_fullname == "accounts.chat_id" for fk in chat_id_col.foreign_keys
    )


def test_product_model_structure():
    assert Product.__tablename__ == "products"
    columns = {col.name: col for col in Product.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "unit" in columns
    assert "is_active" in columns
    assert "available_dates" in columns
    assert columns["unit"].default.arg == "шт"
    assert columns["is_active"].default.arg is True


def test_metadata_ddl_generation_postgresql():
    ddl_statements = []

    def executor(sql, *args, **kwargs):
        ddl_statements.append(str(sql.compile(dialect=mock_engine.dialect)).strip())

    mock_engine = create_mock_engine("postgresql+asyncpg://", executor)
    Base.metadata.create_all(mock_engine)
    combined = "\n".join(ddl_statements)
    assert "CREATE TABLE accounts" in combined
    assert "CREATE TABLE products" in combined
    assert "CREATE TABLE orders" in combined
    assert "FOREIGN KEY(chat_id) REFERENCES accounts (chat_id)" in combined


def test_schemas_order_create_request_valid():
    req = OrderCreateRequest(
        chat_id=12345,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[{"name": "Молоко 1л", "quantity": 2}],
        products_current=[{"name": "Молоко 1л", "quantity": 2}],
    )
    assert req.chat_id == 12345
    assert req.date == date(2026, 12, 31)
    assert len(req.products_max) == 1


def test_schemas_order_create_request_defaults():
    req = OrderCreateRequest(
        chat_id=12345,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
    )
    assert req.products_max == []
    assert req.products_current == []


def test_schemas_order_create_request_russian_date_format():
    req = OrderCreateRequest(
        chat_id=12345,
        date="31.12.2026",
        last_date_before_registration="25.12.2026",
    )
    assert req.date == date(2026, 12, 31)
    assert req.last_date_before_registration == date(2026, 12, 25)


def test_schemas_order_create_request_dict_products():
    req = OrderCreateRequest(
        chat_id=12345,
        date="2026-12-31",
        last_date_before_registration="2026-12-25",
        products_max={"молоко": 2, "сыр": 1},
        products_current={"молоко": 1},
    )
    assert isinstance(req.products_max, dict)
    assert req.products_max["молоко"] == 2


def test_schemas_order_create_request_invalid():
    with pytest.raises(ValidationError):
        OrderCreateRequest(chat_id="not_an_int", date="invalid-date")


def test_schemas_order_response():
    resp = OrderResponse(
        id=1,
        chat_id=123,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[],
        products_current=[],
    )
    assert resp.id == 1
    assert resp.chat_id == 123


def test_schemas_order_user_and_id_requests():
    user_req = OrderUserRequest(chat_id=555)
    assert user_req.chat_id == 555
    id_req = OrderIDRequest(order_id=42)
    assert id_req.order_id == 42


def test_schemas_product_create_and_response():
    create_req = ProductCreateRequest(name="Сыр 300г")
    assert create_req.name == "Сыр 300г"
    assert create_req.unit == "шт"
    assert create_req.is_active is True
    assert create_req.available_dates == []

    resp = ProductResponse(
        id=5,
        name="Творог 200г",
        unit="пачка",
        is_active=True,
        available_dates=["2026-12-31"],
    )
    assert resp.id == 5
    assert resp.unit == "пачка"


def test_schemas_available_products_request():
    req1 = AvailableProductsRequest(order_date="2026-12-31")
    assert req1.order_date == "2026-12-31"
    req2 = AvailableProductsRequest(target_date="31.12.2026")
    assert req2.target_date == "31.12.2026"
    req3 = AvailableProductsRequest()
    assert req3.order_date is None
    assert req3.target_date is None


def test_crud_normalize_date():
    assert _normalize_date("31.12.2026") == date(2026, 12, 31)
    assert _normalize_date("2026-12-31") == date(2026, 12, 31)
    assert _normalize_date(date(2026, 12, 31)) == date(2026, 12, 31)
    with pytest.raises(ValueError):
        _normalize_date("invalid-date-string")


@pytest.mark.asyncio
async def test_crud_create_order():
    session = MockSession()
    order = await create_order(
        chat_id=999,
        order_date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[{"name": "Молоко 1л", "quantity": 1}],
        products_current=[{"name": "Молоко 1л", "quantity": 1}],
        session=session,
    )
    assert order.chat_id == 999
    assert order.id == 100
    assert session.committed is True
    assert len(session.added) == 1
    assert len(session.refreshed) == 1


@pytest.mark.asyncio
async def test_crud_create_order_with_string_dates():
    session = MockSession()
    order = await create_order(
        chat_id=999,
        order_date="31.12.2026",
        last_date_before_registration="25.12.2026",
        products_max={"молоко": 1},
        products_current={"молоко": 1},
        session=session,
    )
    assert order.chat_id == 999
    assert order.date == date(2026, 12, 31)
    assert order.last_date_before_registration == date(2026, 12, 25)


@pytest.mark.asyncio
async def test_crud_create_orders_concurrently():
    sessions = [MockSession() for _ in range(5)]
    tasks = [
        create_order(
            chat_id=1000 + i,
            order_date=date(2026, 12, 31),
            last_date_before_registration=date(2026, 12, 25),
            products_max=[{"id": i}],
            products_current=[{"id": i}],
            session=sessions[i],
        )
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    assert len(results) == 5
    for i, res in enumerate(results):
        assert res.chat_id == 1000 + i
        assert sessions[i].committed is True


@pytest.mark.asyncio
async def test_crud_get_orders_by_chat_id():
    fake_order = Order(
        id=1,
        chat_id=999,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[],
        products_current=[],
    )
    session = MockSession(execute_result=MockQueryResult(items=[fake_order]))
    orders = await get_orders_by_chat_id(999, session=session)
    assert len(orders) == 1
    assert orders[0].chat_id == 999


@pytest.mark.asyncio
async def test_crud_get_all_orders():
    fake_orders = [
        Order(
            id=1,
            chat_id=111,
            date=date(2026, 12, 31),
            last_date_before_registration=date(2026, 12, 25),
            products_max=[],
            products_current=[],
        ),
        Order(
            id=2,
            chat_id=222,
            date=date(2026, 12, 31),
            last_date_before_registration=date(2026, 12, 25),
            products_max=[],
            products_current=[],
        ),
    ]
    session = MockSession(execute_result=MockQueryResult(items=fake_orders))
    orders = await get_all_orders(session=session)
    assert len(orders) == 2


@pytest.mark.asyncio
async def test_crud_get_order_by_id():
    fake_order = Order(
        id=7,
        chat_id=333,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[],
        products_current=[],
    )
    session_found = MockSession(execute_result=MockQueryResult(items=[fake_order]))
    order = await get_order_by_id(7, session=session_found)
    assert order is not None
    assert order.id == 7

    session_empty = MockSession(execute_result=MockQueryResult(items=[]))
    order_none = await get_order_by_id(999, session=session_empty)
    assert order_none is None


@pytest.mark.asyncio
async def test_crud_delete_order_by_id():
    session_deleted = MockSession(execute_result=MockQueryResult(rowcount=1))
    success = await delete_order_by_id(7, session=session_deleted)
    assert success is True
    assert session_deleted.committed is True

    session_not_found = MockSession(execute_result=MockQueryResult(rowcount=0))
    failed = await delete_order_by_id(999, session=session_not_found)
    assert failed is False


@pytest.mark.asyncio
async def test_crud_create_product():
    session = MockSession()
    product = await create_product(
        name="Масло сливочное",
        unit="пачка",
        is_active=True,
        available_dates=["2026-12-31"],
        session=session,
    )
    assert product.name == "Масло сливочное"
    assert product.unit == "пачка"
    assert product.available_dates == ["2026-12-31"]
    assert session.committed is True
    assert len(session.added) == 1


@pytest.mark.asyncio
async def test_crud_get_all_products():
    fake_products = [
        Product(id=1, name="Молоко", unit="шт", is_active=True, available_dates=[]),
        Product(id=2, name="Сыр", unit="шт", is_active=True, available_dates=[]),
    ]
    session = MockSession(execute_result=MockQueryResult(items=fake_products))
    products = await get_all_products(session=session)
    assert len(products) == 2


@pytest.mark.asyncio
async def test_crud_get_available_products():
    p1 = Product(id=1, name="Молоко", unit="шт", is_active=True, available_dates=[])
    p2 = Product(
        id=2,
        name="Творог",
        unit="шт",
        is_active=True,
        available_dates=["2026-12-31", "31.12.2026"],
    )
    p3 = Product(
        id=3,
        name="Сметана",
        unit="шт",
        is_active=True,
        available_dates=["2026-12-25"],
    )
    p4 = Product(
        id=4,
        name="Кефир",
        unit="шт",
        is_active=True,
        available_dates="2026-12-31",
    )
    p5 = Product(
        id=5,
        name="Ряженка",
        unit="шт",
        is_active=True,
        available_dates=["2026-12-31T12:00:00"],
    )
    session = MockSession(execute_result=MockQueryResult(items=[p1, p2, p3, p4, p5]))

    all_active = await get_available_products(target_date=None, session=session)
    assert len(all_active) == 5

    for_new_year = await get_available_products(
        target_date="2026-12-31", session=session
    )
    assert p1 in for_new_year
    assert p2 in for_new_year
    assert p4 in for_new_year
    assert p5 in for_new_year
    assert p3 not in for_new_year

    for_new_year_ru = await get_available_products(
        target_date="31.12.2026", session=session
    )
    assert p2 in for_new_year_ru
    assert p4 in for_new_year_ru

    for_date_obj = await get_available_products(
        target_date=date(2026, 12, 31), session=session
    )
    assert len(for_date_obj) == 4

    unparseable_target = await get_available_products(
        target_date="not-a-real-date", session=session
    )
    assert len(unparseable_target) == 1
    assert p1 in unparseable_target


@pytest.mark.asyncio
async def test_crud_get_session_fallback():
    mock_session_obj = MockSession()

    @asynccontextmanager
    async def mock_async_session():
        yield mock_session_obj

    with patch("order_service.crud.async_session", mock_async_session):
        async with _get_session() as s:
            assert s is mock_session_obj


@pytest.mark.asyncio
async def test_api_health():
    async with AsyncClient(
        transport=ASGITransport(app=fapp), base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_order_create():
    fake_order = Order(
        id=77,
        chat_id=123,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[{"name": "Молоко", "quantity": 1}],
        products_current=[{"name": "Молоко", "quantity": 1}],
    )
    with patch(
        "order_service.__main__.create_order", AsyncMock(return_value=fake_order)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            payload = {
                "chat_id": 123,
                "date": "2026-12-31",
                "last_date_before_registration": "2026-12-25",
                "products_max": [{"name": "Молоко", "quantity": 1}],
                "products_current": [{"name": "Молоко", "quantity": 1}],
            }
            response = await ac.post("/order_create", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["id"] == 77
            assert data["order"]["chat_id"] == 123


@pytest.mark.asyncio
async def test_api_order_create_russian_date_and_dict_products():
    fake_order = Order(
        id=88,
        chat_id=456,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max={"молоко": 2},
        products_current={"молоко": 2},
    )
    with patch(
        "order_service.__main__.create_order", AsyncMock(return_value=fake_order)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            payload = {
                "chat_id": 456,
                "date": "31.12.2026",
                "last_date_before_registration": "25.12.2026",
                "products_max": {"молоко": 2},
                "products_current": {"молоко": 2},
            }
            response = await ac.post("/order_create", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["id"] == 88
            assert data["order"]["products_max"] == {"молоко": 2}


@pytest.mark.asyncio
async def test_api_order_create_invalid_payload():
    async with AsyncClient(
        transport=ASGITransport(app=fapp), base_url="http://test"
    ) as ac:
        response = await ac.post("/order_create", json={"invalid": "payload"})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_orders_get():
    fake_order = Order(
        id=77,
        chat_id=123,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[],
        products_current=[],
    )
    with patch(
        "order_service.__main__.get_orders_by_chat_id",
        AsyncMock(return_value=[fake_order]),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/orders_get", json={"chat_id": 123})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["orders"]) == 1
            assert data["orders"][0]["id"] == 77


@pytest.mark.asyncio
async def test_api_all_orders_get():
    fake_order = Order(
        id=10,
        chat_id=555,
        date=date(2026, 11, 20),
        last_date_before_registration=date(2026, 11, 15),
        products_max=[],
        products_current=[{"name": "Сыр 300г", "quantity": 1}],
    )
    with patch(
        "order_service.__main__.get_all_orders", AsyncMock(return_value=[fake_order])
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/all_orders_get")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["orders"]) == 1
            assert data["orders"][0]["chat_id"] == 555


@pytest.mark.asyncio
async def test_api_order_get_success():
    fake_order = Order(
        id=42,
        chat_id=777,
        date=date(2026, 12, 31),
        last_date_before_registration=date(2026, 12, 25),
        products_max=[{"name": "Творог", "quantity": 1}],
        products_current=[{"name": "Творог", "quantity": 1}],
    )
    with patch(
        "order_service.__main__.get_order_by_id", AsyncMock(return_value=fake_order)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/order_get", json={"order_id": 42})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["order"]["id"] == 42
            assert data["order"]["chat_id"] == 777


@pytest.mark.asyncio
async def test_api_order_get_not_found():
    with patch("order_service.__main__.get_order_by_id", AsyncMock(return_value=None)):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/order_get", json={"order_id": 999})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert data["message"] == "Заказ не найден"


@pytest.mark.asyncio
async def test_api_order_delete_success():
    with patch(
        "order_service.__main__.delete_order_by_id", AsyncMock(return_value=True)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/order_delete", json={"order_id": 10})
            assert response.status_code == 200
            assert response.json() == {"status": "success"}


@pytest.mark.asyncio
async def test_api_order_delete_not_found():
    with patch(
        "order_service.__main__.delete_order_by_id", AsyncMock(return_value=False)
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/order_delete", json={"order_id": 999})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert data["message"] == "Заказ не найден"


@pytest.mark.asyncio
async def test_api_order_delete_invalid_payload():
    async with AsyncClient(
        transport=ASGITransport(app=fapp), base_url="http://test"
    ) as ac:
        response = await ac.post("/order_delete", json={"not_order_id": "bad"})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_products_get():
    p1 = Product(id=1, name="Молоко 1л", unit="шт", is_active=True, available_dates=[])
    p2 = Product(
        id=2, name="Творог 200г", unit="шт", is_active=True, available_dates=[]
    )
    with patch(
        "order_service.__main__.get_available_products",
        AsyncMock(return_value=[p1, p2]),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            response = await ac.post("/products_get", json={"order_date": "31.12.2026"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["products"]) == 2
            assert data["products"][0]["name"] == "Молоко 1л"

            response_no_body = await ac.post("/products_get")
            assert response_no_body.status_code == 200
            assert len(response_no_body.json()["products"]) == 2


@pytest.mark.asyncio
async def test_api_product_create():
    p = Product(
        id=15,
        name="Йогурт",
        unit="шт",
        is_active=True,
        available_dates=["2026-12-31"],
    )
    with patch("order_service.__main__.create_product", AsyncMock(return_value=p)):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            payload = {
                "name": "Йогурт",
                "unit": "шт",
                "is_active": True,
                "available_dates": ["2026-12-31"],
            }
            response = await ac.post("/product_create", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["product"]["id"] == 15
            assert data["product"]["name"] == "Йогурт"


@pytest.mark.asyncio
async def test_app_lifespan():
    mock_conn = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn

    with patch("order_service.__main__.engine", mock_engine):
        async with lifespan(fapp):
            pass
        mock_conn.run_sync.assert_called_once_with(Base.metadata.create_all)


def test_metadata_ddl_generation_sqlite():
    ddl_statements = []

    def executor(sql, *args, **kwargs):
        ddl_statements.append(str(sql.compile(dialect=mock_engine.dialect)).strip())

    mock_engine = create_mock_engine("sqlite://", executor)
    Base.metadata.create_all(mock_engine)
    combined = "\n".join(ddl_statements)
    assert "CREATE TABLE accounts" in combined
    assert "CREATE TABLE products" in combined
    assert "CREATE TABLE orders" in combined


@pytest.mark.asyncio
async def test_crud_sql_statement_clauses():
    session = MockSession(execute_result=MockQueryResult(items=[], rowcount=1))

    await get_orders_by_chat_id(888, session=session)
    compiled_orders = str(
        session.last_statement.compile(
            dialect=create_mock_engine(
                "postgresql+asyncpg://", lambda *a, **k: None
            ).dialect
        )
    )
    assert "orders.chat_id =" in compiled_orders
    assert "ORDER BY orders.id DESC" in compiled_orders

    await get_order_by_id(77, session=session)
    compiled_get_one = str(
        session.last_statement.compile(
            dialect=create_mock_engine(
                "postgresql+asyncpg://", lambda *a, **k: None
            ).dialect
        )
    )
    assert "orders.id =" in compiled_get_one

    await delete_order_by_id(99, session=session)
    compiled_delete = str(
        session.last_statement.compile(
            dialect=create_mock_engine(
                "postgresql+asyncpg://", lambda *a, **k: None
            ).dialect
        )
    )
    assert "orders.id =" in compiled_delete

    await get_available_products(session=session)
    compiled_prods = str(
        session.last_statement.compile(
            dialect=create_mock_engine(
                "postgresql+asyncpg://", lambda *a, **k: None
            ).dialect
        )
    )
    assert (
        "products.is_active = true" in compiled_prods.lower()
        or "is_active is true" in compiled_prods.lower()
    )


@pytest.mark.asyncio
async def test_crud_inactive_products_filtered_out():
    active_prod = Product(
        id=1, name="Активный товар", is_active=True, available_dates=[]
    )
    inactive_prod = Product(
        id=2, name="Неактивный товар", is_active=False, available_dates=[]
    )
    session = MockSession(
        execute_result=MockQueryResult(items=[active_prod, inactive_prod])
    )

    products = await get_available_products(target_date="2026-12-31", session=session)
    assert active_prod in products
    assert inactive_prod not in products


def test_schema_and_crud_extended_date_formats():
    iso_with_time = "2026-12-31T15:30:00"
    space_with_time = "2026-12-31 15:30:00"
    dash_ru = "31-12-2026"
    slash_iso = "2026/12/31"
    slash_ru = "31/12/2026"

    for val in (iso_with_time, space_with_time, dash_ru, slash_iso, slash_ru):
        assert _normalize_date(val) == date(2026, 12, 31)

    req = OrderCreateRequest(
        chat_id=123,
        date="2026-12-31T12:00:00",
        last_date_before_registration="25-12-2026",
    )
    assert req.date == date(2026, 12, 31)
    assert req.last_date_before_registration == date(2026, 12, 25)


def test_schema_order_deadline_validation():
    with pytest.raises(ValidationError):
        OrderCreateRequest(
            chat_id=123,
            date="2026-12-10",
            last_date_before_registration="2026-12-20",
        )

    same_day = OrderCreateRequest(
        chat_id=123,
        date="2026-12-20",
        last_date_before_registration="2026-12-20",
    )
    assert same_day.date == same_day.last_date_before_registration


def test_schema_product_name_validation():
    with pytest.raises(ValidationError):
        ProductCreateRequest(name="")

    with pytest.raises(ValidationError):
        ProductCreateRequest(name="   ")

    prod = ProductCreateRequest(name="  Сметана  ")
    assert prod.name == "Сметана"


def test_large_jsonb_products_payload():
    large_list = [
        {"id": i, "name": f"Товар #{i}", "quantity": i % 10 + 1} for i in range(500)
    ]
    req = OrderCreateRequest(
        chat_id=99999,
        date="2026-12-31",
        last_date_before_registration="2026-12-25",
        products_max=large_list,
        products_current=large_list,
    )
    assert len(req.products_max) == 500
    assert len(req.products_current) == 500


@pytest.mark.asyncio
async def test_api_endpoints_error_handling():
    with patch(
        "order_service.__main__.create_order",
        AsyncMock(side_effect=RuntimeError("DB write failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post(
                "/order_create",
                json={
                    "chat_id": 1,
                    "date": "2026-12-31",
                    "last_date_before_registration": "2026-12-25",
                },
            )
            assert res.status_code == 200
            assert res.json()["status"] == "error"
            assert "DB write failure" in res.json()["message"]

    with patch(
        "order_service.__main__.get_orders_by_chat_id",
        AsyncMock(side_effect=RuntimeError("DB query failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post("/orders_get", json={"chat_id": 1})
            assert res.status_code == 200
            assert res.json()["status"] == "error"
            assert res.json()["orders"] == []

    with patch(
        "order_service.__main__.get_all_orders",
        AsyncMock(side_effect=RuntimeError("DB query failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post("/all_orders_get")
            assert res.status_code == 200
            assert res.json()["status"] == "error"
            assert res.json()["orders"] == []

    with patch(
        "order_service.__main__.get_order_by_id",
        AsyncMock(side_effect=RuntimeError("DB query failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post("/order_get", json={"order_id": 1})
            assert res.status_code == 200
            assert res.json()["status"] == "error"

    with patch(
        "order_service.__main__.delete_order_by_id",
        AsyncMock(side_effect=RuntimeError("DB delete failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post("/order_delete", json={"order_id": 1})
            assert res.status_code == 200
            assert res.json()["status"] == "error"

    with patch(
        "order_service.__main__.get_available_products",
        AsyncMock(side_effect=RuntimeError("DB query failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post("/products_get")
            assert res.status_code == 200
            assert res.json()["status"] == "error"
            assert res.json()["products"] == []

    with patch(
        "order_service.__main__.create_product",
        AsyncMock(side_effect=RuntimeError("DB write failure")),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fapp), base_url="http://test"
        ) as ac:
            res = await ac.post("/product_create", json={"name": "Молоко"})
            assert res.status_code == 200
            assert res.json()["status"] == "error"


@pytest.mark.asyncio
async def test_crud_session_rollback_on_error():
    mock_session = MockSession()
    with pytest.raises(ZeroDivisionError):
        async with _get_session(mock_session):
            raise ZeroDivisionError("Forced error")
    assert mock_session.rolled_back is True
