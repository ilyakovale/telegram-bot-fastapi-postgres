from sqlalchemy import BigInteger, Boolean, Column, String

try:
    from account_service.database import Base
except (ImportError, ModuleNotFoundError):
    from database import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = {"extend_existing": True}

    chat_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    block = Column(Boolean, default=False)
