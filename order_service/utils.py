from sqlalchemy import Table, Column, BigInteger, String, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from .database import engine

metadata = MetaData()

def CreateOrderDetailTable(order_date: str):
    table_name = order_date
    table = Table(
        table_name,
        metadata,
        Column("chat_id", BigInteger,primary_key=True, nullable=False),
        Column("quantity", JSONB, nullable=False, default=list),
        Column("comment", String, nullable=True),
    )

    metadata.create_all(engine, tables=[table], checkfirst=True)
    return table