from sqlalchemy import select
from database import async_session
from models import Account

async def get_all_accounts():
    async with async_session() as session:
        result = await session.execute(select(Account))
        return result.scalars().all()