from sqlalchemy import Column, Integer, String, BigInteger
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    chat_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    address = Column(String)
    phone_number = Column(String)