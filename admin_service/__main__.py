import asyncio
import uvicorn
from fastapi import FastAPI
from database import engine, Base
from crud import get_all_accounts
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
    yield

fapp = FastAPI(title="Admin Microservice", lifespan=lifespan)

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
    

if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8003)