import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from config import GetAccountMessageRequest, SetAccountMessageRequest, CheckAccountMessageRequest
from database import engine, Base
from crud import get_account, set_account,check_account, get_all_accounts


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
    yield

fapp = FastAPI(title="Account Microservice", lifespan=lifespan)


@fapp.post("/account_get")
async def account_get(request: GetAccountMessageRequest):
    account = await get_account(request.chat_id)
    if not account:
        return {"status": "Аккаунт не найден"}
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

@fapp.post("/all_accounts_get") 
async def all_accounts_get():
    accounts = await get_all_accounts()
    accounts_data = []
    for acc in accounts:
        accounts_data.append({
            "id": acc.chat_id,
            "name": acc.name,           
            "address": acc.address,      
            "phone_number": acc.phone_number,
        })
        
    return {
        "status": "success",
        "accounts": accounts_data,
    }

@fapp.post("/account_check")
async def account_check(request: CheckAccountMessageRequest):
    exists = await check_account(request.chat_id)
    return {"exists": exists}

if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8001)