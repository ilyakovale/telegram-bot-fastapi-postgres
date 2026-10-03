from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, select

try:
    from database import async_session
    from models import Order, Product
except (ImportError, ModuleNotFoundError):
    from order_service.database import async_session
    from order_service.models import Order, Product


@asynccontextmanager
async def _get_session(session=None):
    if session is not None:
        yield session
    else:
        async with async_session() as s:
            yield s


async def create_order(
    chat_id: int,
    order_date: date,
    last_date_before_registration: date,
    products_max: list[Any] | dict[str, Any],
    products_current: list[Any] | dict[str, Any],
    session=None,
) -> Order:
    async with _get_session(session) as s:
        order = Order(
            chat_id=chat_id,
            date=order_date,
            last_date_before_registration=last_date_before_registration,
            products_max=products_max,
            products_current=products_current,
        )
        s.add(order)
        await s.commit()
        await s.refresh(order)
        return order


async def get_orders_by_chat_id(chat_id: int, session=None) -> list[Order]:
    async with _get_session(session) as s:
        result = await s.execute(
            select(Order).where(Order.chat_id == chat_id).order_by(Order.id.desc())
        )
        return list(result.scalars().all())


async def get_all_orders(session=None) -> list[Order]:
    async with _get_session(session) as s:
        result = await s.execute(select(Order).order_by(Order.id.desc()))
        return list(result.scalars().all())


async def get_order_by_id(order_id: int, session=None) -> Order | None:
    async with _get_session(session) as s:
        result = await s.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()


async def delete_order_by_id(order_id: int, session=None) -> bool:
    async with _get_session(session) as s:
        result = await s.execute(delete(Order).where(Order.id == order_id))
        await s.commit()
        return result.rowcount > 0


async def create_product(
    name: str,
    unit: str = "шт",
    is_active: bool = True,
    available_dates: list[Any] | None = None,
    session=None,
) -> Product:
    async with _get_session(session) as s:
        product = Product(
            name=name,
            unit=unit,
            is_active=is_active,
            available_dates=available_dates if available_dates is not None else [],
        )
        s.add(product)
        await s.commit()
        await s.refresh(product)
        return product


async def get_all_products(session=None) -> list[Product]:
    async with _get_session(session) as s:
        result = await s.execute(select(Product).order_by(Product.id.asc()))
        return list(result.scalars().all())


async def get_available_products(
    target_date: date | str | None = None,
    session=None,
) -> list[Product]:
    async with _get_session(session) as s:
        result = await s.execute(
            select(Product).where(Product.is_active == True).order_by(Product.id.asc())
        )
        products = list(result.scalars().all())
        if not target_date:
            return products

        target_candidates = set()
        if isinstance(target_date, (date, datetime)):
            target_candidates.add(target_date.strftime("%Y-%m-%d"))
            target_candidates.add(target_date.strftime("%d.%m.%Y"))
        elif isinstance(target_date, str):
            clean_str = target_date.strip()
            if clean_str:
                target_candidates.add(clean_str)
                if "-" in clean_str:
                    parts = clean_str.split("-")
                    if len(parts) == 3:
                        try:
                            d = date(int(parts[0]), int(parts[1]), int(parts[2]))
                            target_candidates.add(d.strftime("%Y-%m-%d"))
                            target_candidates.add(d.strftime("%d.%m.%Y"))
                        except ValueError:
                            pass
                elif "." in clean_str:
                    parts = clean_str.split(".")
                    if len(parts) == 3:
                        try:
                            d = date(int(parts[2]), int(parts[1]), int(parts[0]))
                            target_candidates.add(d.strftime("%Y-%m-%d"))
                            target_candidates.add(d.strftime("%d.%m.%Y"))
                        except ValueError:
                            pass

        if not target_candidates:
            return products

        filtered = []
        for product in products:
            dates = product.available_dates
            if not dates:
                filtered.append(product)
                continue
            if any(str(d).strip() in target_candidates for d in dates):
                filtered.append(product)
        return filtered
