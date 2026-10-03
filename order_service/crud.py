from contextlib import asynccontextmanager
from datetime import date
from typing import Any

from sqlalchemy import delete, select

try:
    from database import async_session
    from models import Order, Product
    from schemas import parse_date
except (ImportError, ModuleNotFoundError):
    from order_service.database import async_session
    from order_service.models import Order, Product
    from order_service.schemas import parse_date


def _normalize_date(val: date | str) -> date:
    parsed = parse_date(val)
    if parsed is not None:
        return parsed
    raise ValueError(f"Invalid date: {val}")


@asynccontextmanager
async def _get_session(session=None):
    if session is not None:
        try:
            yield session
        except Exception:
            if hasattr(session, "rollback"):
                await session.rollback()
            raise
    else:
        async with async_session() as s:
            try:
                yield s
            except Exception:
                await s.rollback()
                raise


async def create_order(
    chat_id: int,
    order_date: date | str,
    last_date_before_registration: date | str,
    products_max: list[Any] | dict[str, Any],
    products_current: list[Any] | dict[str, Any],
    session=None,
) -> Order:
    parsed_date = _normalize_date(order_date)
    parsed_last_date = _normalize_date(last_date_before_registration)
    async with _get_session(session) as s:
        order = Order(
            chat_id=chat_id,
            date=parsed_date,
            last_date_before_registration=parsed_last_date,
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
        return bool(result.rowcount and result.rowcount > 0)


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
            select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.id.asc())
        )
        products = list(result.scalars().all())
        if not target_date:
            return products

        target_dt = parse_date(target_date)
        raw_target_str = str(target_date).strip() if target_date else ""

        filtered = []
        for product in products:
            if not getattr(product, "is_active", True):
                continue
            dates = product.available_dates
            if not dates:
                filtered.append(product)
                continue
            if isinstance(dates, str) or not isinstance(dates, (list, tuple, set)):
                dates = [dates]
            matched = False
            for d in dates:
                d_dt = parse_date(d)
                if target_dt is not None and d_dt is not None and d_dt == target_dt:
                    matched = True
                    break
                if (
                    raw_target_str
                    and str(d).strip().split("T")[0].split(" ")[0]
                    == raw_target_str.split("T")[0].split(" ")[0]
                ):
                    matched = True
                    break
            if matched:
                filtered.append(product)
        return filtered
