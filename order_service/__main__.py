from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

try:
    from crud import (
        create_order,
        create_product,
        delete_order_by_id,
        get_all_orders,
        get_available_products,
        get_orders_by_chat_id,
    )
    from database import Base, engine
    from schemas import (
        AvailableProductsRequest,
        OrderCreateRequest,
        OrderIDRequest,
        OrderUserRequest,
        ProductCreateRequest,
    )
except (ImportError, ModuleNotFoundError):
    from order_service.crud import (
        create_order,
        create_product,
        delete_order_by_id,
        get_all_orders,
        get_available_products,
        get_orders_by_chat_id,
    )
    from order_service.database import Base, engine
    from order_service.schemas import (
        AvailableProductsRequest,
        OrderCreateRequest,
        OrderIDRequest,
        OrderUserRequest,
        ProductCreateRequest,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


fapp = FastAPI(title="Order Microservice", lifespan=lifespan)
app = fapp


@fapp.get("/health")
async def health():
    return {"status": "ok"}


@fapp.post("/order_create")
async def handle_order_create(request: OrderCreateRequest):
    order = await create_order(
        chat_id=request.chat_id,
        order_date=request.date,
        last_date_before_registration=request.last_date_before_registration,
        products_max=request.products_max,
        products_current=request.products_current,
    )
    return {
        "status": "success",
        "id": order.id,
        "order": {
            "id": order.id,
            "chat_id": order.chat_id,
            "date": str(order.date),
            "last_date_before_registration": str(order.last_date_before_registration),
            "products_max": order.products_max,
            "products_current": order.products_current,
        },
    }


@fapp.post("/orders_get")
async def handle_orders_get(request: OrderUserRequest):
    orders = await get_orders_by_chat_id(request.chat_id)
    orders_data = [
        {
            "id": o.id,
            "chat_id": o.chat_id,
            "date": str(o.date),
            "last_date_before_registration": str(o.last_date_before_registration),
            "products_max": o.products_max,
            "products_current": o.products_current,
        }
        for o in orders
    ]
    return {"status": "success", "orders": orders_data}


@fapp.post("/all_orders_get")
async def handle_all_orders_get():
    orders = await get_all_orders()
    orders_data = [
        {
            "id": o.id,
            "chat_id": o.chat_id,
            "date": str(o.date),
            "last_date_before_registration": str(o.last_date_before_registration),
            "products_max": o.products_max,
            "products_current": o.products_current,
        }
        for o in orders
    ]
    return {"status": "success", "orders": orders_data}


@fapp.post("/order_delete")
async def handle_order_delete(request: OrderIDRequest):
    deleted = await delete_order_by_id(request.order_id)
    if not deleted:
        return {"status": "error", "message": "Заказ не найден"}
    return {"status": "success"}


@fapp.post("/products_get")
async def handle_products_get(request: AvailableProductsRequest | None = None):
    target_date = None
    if request:
        target_date = request.order_date or request.target_date
    products = await get_available_products(target_date)
    products_data = [
        {
            "id": p.id,
            "name": p.name,
            "unit": p.unit,
            "is_active": p.is_active,
            "available_dates": p.available_dates,
        }
        for p in products
    ]
    return {"status": "success", "products": products_data}


@fapp.post("/product_create")
async def handle_product_create(request: ProductCreateRequest):
    product = await create_product(
        name=request.name,
        unit=request.unit,
        is_active=request.is_active,
        available_dates=request.available_dates,
    )
    return {
        "status": "success",
        "product": {
            "id": product.id,
            "name": product.name,
            "unit": product.unit,
            "is_active": product.is_active,
            "available_dates": product.available_dates,
        },
    }


if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8002)
