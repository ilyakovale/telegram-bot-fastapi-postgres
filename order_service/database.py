from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

try:
    from config import DB_URL
except (ImportError, ModuleNotFoundError):
    from order_service.config import DB_URL

engine = create_async_engine(DB_URL, echo=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
