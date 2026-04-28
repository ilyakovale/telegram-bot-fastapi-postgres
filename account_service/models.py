from sqlalchemy import Column, Integer, String, BigInteger
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True)
    name = Column(String)
    address = Column(String)
    phone_number = Column(String)