from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

try:
    from config import AccountID, GetAccountMessageRequest, SetAccountMessageRequest
    from crud import (
        block_account,
        check_account,
        get_account,
        get_all_accounts,
        set_account,
        unblock_account,
    )
    from database import Base, engine
except (ImportError, ModuleNotFoundError):
    from account_service.config import (
        AccountID,
        GetAccountMessageRequest,
        SetAccountMessageRequest,
    )
    from account_service.crud import (
        block_account,
        check_account,
        get_account,
        get_all_accounts,
        set_account,
        unblock_account,
    )
    from account_service.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


fapp = FastAPI(title="Account Microservice", lifespan=lifespan)


@fapp.get("/health")
async def health():
    return {"status": "ok"}


@fapp.post("/account_get")
async def account_get(request: GetAccountMessageRequest):
    account = await get_account(request.chat_id)
    if not account:
        return {"status": "Аккаунт не найден"}
    return {
        "status": "Данные отправлены",
        "name": account.name,
        "address": account.address,
        "phone_number": account.phone_number,
    }


@fapp.post("/account_set")
async def account_set(request: SetAccountMessageRequest):
    await set_account(
        request.chat_id,
        request.name,
        request.address,
        request.phone_number,
    )
    return {"status": "Данные записаны"}


@fapp.post("/all_accounts_get")
async def all_accounts_get():
    accounts = await get_all_accounts()
    accounts_data = []
    for acc in accounts:
        accounts_data.append(
            {
                "chat_id": acc.chat_id,
                "name": acc.name,
                "address": acc.address,
                "phone_number": acc.phone_number,
                "block": acc.block,
            }
        )

    return {
        "status": "success",
        "accounts": accounts_data,
    }


@fapp.post("/account_check")
async def account_check(request: AccountID):
    exists = await check_account(request.chat_id)
    return {"exists": exists}


@fapp.post("/account_block")
async def account_block(request: AccountID):
    exists = await block_account(request.chat_id)
    return {"exists": exists}


@fapp.post("/account_unblock")
async def account_unblock(request: AccountID):
    exists = await unblock_account(request.chat_id)
    return {"exists": exists}


if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8001)
