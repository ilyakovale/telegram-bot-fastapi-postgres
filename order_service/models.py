from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB

try:
    from database import Base
except (ImportError, ModuleNotFoundError):
    from order_service.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("accounts.chat_id"), nullable=False)
    date = Column(Date, nullable=False)
    last_date_before_registration = Column(Date, nullable=False)
    products_max = Column(JSONB, nullable=False, default=list)
    products_current = Column(JSONB, nullable=False, default=list)


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    unit = Column(String, default="шт")
    is_active = Column(Boolean, default=True)
    available_dates = Column(JSONB, default=list)
