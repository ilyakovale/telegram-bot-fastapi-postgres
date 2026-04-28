from sqlalchemy import select
from database import async_session
from models import Account

async def check_account(chat_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(Account.chat_id == chat_id)
        )
        return result.scalar_one_or_none() is not None

async def get_account(chat_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(Account.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

async def get_account(chat_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(Account.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

async def set_account(chat_id: int, name: str, address: str, phone_number: str):
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(Account.chat_id == chat_id)
        )
        account = result.scalar_one_or_none()

        if account:
            account.name = name
            account.address = address
            account.phone_number = phone_number
            account.verify = False 
        else:
            session.add(Account(
                chat_id=chat_id,
                name=name,
                address=address,
                phone_number=phone_number
            ))
        await session.commit()