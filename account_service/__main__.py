import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx
from config import GetAccountMessageRequest, SetAccountMessageRequest

fapp = FastAPI(title="Account Microservice")


TELEGRAM_BOT_URL = "http://gs:8000"

@fapp.post("/account_get") 
async def get_account(request: GetAccountMessageRequest):
    return {
        "status": "Данные отправлены",
        "name": "ivan ivanov",
        "address": "pushkina",
        "phone_number": "+375 00 000 00 00",
        }
    
@fapp.post("/account_set") 
async def set_account(request: SetAccountMessageRequest):
    return {
        "status": "Данные записаны"
    }


if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8001)