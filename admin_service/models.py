from sqlalchemy import Column, String, BigInteger, Boolean
from database import Base

class Account(Base):
    __tablename__ = "accounts"

    chat_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    verify = Column(Boolean, default=False)
    rating = Column(String, default="0")
    
