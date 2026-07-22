from sqlalchemy import Column, String, BigInteger, Boolean, Date
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    chat_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    verify = Column(Boolean, default=False)
    rating = Column(String, default="0")

class Order(Base):
    __tablename__ = "orders"

    date = Column(Date, primary_key=True)
    last_day_before_registration = Column(Date, nullable=False)
    products = Column(JSONB, nullable=False, default=list)
    