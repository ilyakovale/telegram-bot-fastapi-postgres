from contextlib import asynccontextmanager
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from order_service.__main__ import fapp, lifespan
from order_service.crud import (
    _get_session,
    create_order,
    create_product,
    delete_order_by_id,
    get_all_orders,
    get_all_products,
    get_available_products,
    get_order_by_id,
    get_orders_by_chat_id,
)
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

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = 100

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = 100

    async def execute(self, statement):
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


def test_product_model_structure():
    assert Product.__tablename__ == "products"
    columns = {col.name: col for col in Product.__table__.columns}
    assert "id" in columns
    assert "name" in columns
    assert "unit" in columns
    assert "is_active" in columns
    assert "available_dates" in columns


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
    session = MockSession(execute_result=MockQueryResult(items=[p1, p2, p3]))

    all_active = await get_available_products(target_date=None, session=session)
    assert len(all_active) == 3

    for_new_year = await get_available_products(
        target_date="2026-12-31", session=session
    )
    assert len(for_new_year) == 2
    assert p1 in for_new_year
    assert p2 in for_new_year
    assert p3 not in for_new_year

    for_new_year_ru = await get_available_products(
        target_date="31.12.2026", session=session
    )
    assert len(for_new_year_ru) == 2
    assert p2 in for_new_year_ru

    for_date_obj = await get_available_products(
        target_date=date(2026, 12, 31), session=session
    )
    assert len(for_date_obj) == 2


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
        mock_conn.run_sync.assert_called_once()
