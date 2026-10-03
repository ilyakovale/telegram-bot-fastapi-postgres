from sqlalchemy import BigInteger, Boolean, Column, String

try:
    from database import Base
except (ImportError, ModuleNotFoundError):
    from account_service.database import Base


class Account(Base):
    __tablename__ = "accounts"

    chat_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    block = Column(Boolean, default=False)
