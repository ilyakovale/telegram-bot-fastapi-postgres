import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx

class OrderMessageReques(BaseModel):
    chat_id: int
    command: str

fapp = FastAPI(title="Account Microservice")


TELEGRAM_BOT_URL = "http://gs:8000"

@fapp.post("/account") 
async def get_account(request: OrderMessageReques):
    
    if (request.command == "get_info"):
        return {
            "status": "Данные отправлены",
            "name": "ivan ivanov",
            "address": "pushkina",
            "phone_number": "+375 00 000 00 00",
        }
    
    elif (request.command == "input_info"):
        return {
            "status": "Данные записаны"
        }

@fapp.get("/health")
async def health():
    return {"status": "healthy", "service": "Account Microservice"}

if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8002)