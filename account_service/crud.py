from contextlib import asynccontextmanager

from sqlalchemy import select

try:
    from database import async_session
    from models import Account
except (ImportError, ModuleNotFoundError):
    from account_service.database import async_session
    from account_service.models import Account


@asynccontextmanager
async def _get_session(session=None):
    if session is not None:
        yield session
    else:
        async with async_session() as s:
            yield s


async def check_account(chat_id: int, session=None) -> bool:
    async with _get_session(session) as s:
        result = await s.execute(select(Account).where(Account.chat_id == chat_id))
        return result.scalar_one_or_none() is not None


async def get_account(chat_id: int, session=None) -> Account | None:
    async with _get_session(session) as s:
        result = await s.execute(select(Account).where(Account.chat_id == chat_id))
        return result.scalar_one_or_none()


async def get_all_accounts(session=None) -> list[Account]:
    async with _get_session(session) as s:
        result = await s.execute(select(Account))
        return list(result.scalars().all())


async def set_account(
    chat_id: int, name: str, address: str, phone_number: str, session=None
) -> Account:
    async with _get_session(session) as s:
        result = await s.execute(select(Account).where(Account.chat_id == chat_id))
        account = result.scalar_one_or_none()

        if account:
            account.name = name
            account.address = address
            account.phone_number = phone_number
        else:
            account = Account(
                chat_id=chat_id,
                name=name,
                address=address,
                phone_number=phone_number,
            )
            s.add(account)
        await s.commit()
        return account


async def block_account(chat_id: int, session=None) -> bool:
    async with _get_session(session) as s:
        result = await s.execute(select(Account).where(Account.chat_id == chat_id))
        account = result.scalar_one_or_none()
        if account:
            account.block = True
            await s.commit()
            return True
        return False


async def unblock_account(chat_id: int, session=None) -> bool:
    async with _get_session(session) as s:
        result = await s.execute(select(Account).where(Account.chat_id == chat_id))
        account = result.scalar_one_or_none()
        if account:
            account.block = False
            await s.commit()
            return True
        return False


async def check_block_account(chat_id: int, session=None) -> bool:
    async with _get_session(session) as s:
        result = await s.execute(select(Account).where(Account.chat_id == chat_id))
        account = result.scalar_one_or_none()
        return account.block if account else False
