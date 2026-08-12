from sqlalchemy import Column, Date, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("accounts.chat_id"), nullable=False)
    date = Column(Date, nullable=False)
    last_date_before_registration = Column(Date, nullable=False)
    products_max = Column(JSONB, nullable=False, default=list)
    products_current = Column(JSONB, nullable=False, default=list)
