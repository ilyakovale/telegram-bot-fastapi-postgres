import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from config import GetAccountMessageRequest, SetAccountMessageRequest
from database import engine, Base
from crud import get_account, set_account


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # создаём таблицы при старте
    yield

fapp = FastAPI(title="Account Microservice", lifespan=lifespan)


@fapp.post("/account_get")
async def account_get(request: GetAccountMessageRequest):
    account = await get_account(request.chat_id)
    if not account:
        return {"status": "error", "message": "Аккаунт не найден"}
    return {
        "status": "Данные отправлены",
        "name": account.name,
        "address": account.address,
        "phone_number": account.phone_number
    }


@fapp.post("/account_set")
async def account_set(request: SetAccountMessageRequest):
    await set_account(
        request.chat_id,
        request.name,
        request.address,
        request.phone_number
    )
    return {"status": "Данные записаны"}


if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8001)