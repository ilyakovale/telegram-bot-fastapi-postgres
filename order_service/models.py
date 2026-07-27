from sqlalchemy import Column, Date
from sqlalchemy.dialects.postgresql import JSONB
from database import Base, engine

class Order(Base):
    __tablename__ = "orders"

    date = Column(Date, primary_key=True)
    last_date_before_registration = Column(Date, nullable=False)
    products_max = Column(JSONB, nullable=False, default=list)
    products_current = Column(JSONB, nullable=False, default=list)



    