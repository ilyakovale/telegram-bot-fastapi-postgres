import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx
from config import AccountMessageRequest

fapp = FastAPI(title="Account Microservice")


TELEGRAM_BOT_URL = "http://localhost:8000"

@fapp.post("/get_account") 
async def get_account(request: AccountMessageRequest):
    """ПРИНИМАЕТ запрос от бота и выводит в консоль"""
    
    # Выводим в консоль информацию о полученном запросе
    print("=" * 50)
    print(f"📥 Получен запрос от бота!")
    print(f"   chat_id: {request.chat_id}")
    print(f"   text: {request.text}")
    print(f"   parse_mode: {request.parse_mode}")
    print("=" * 50)
    
    # Возвращаем простой ответ
    return {
        "status": "success",
        "message": f"Ваш запрос '{request.text}' получен",
        "chat_id": request.chat_id
    }

@fapp.get("/health")
async def health():
    return {"status": "healthy", "service": "Account Microservice"}

if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8001)