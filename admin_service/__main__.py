import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
import httpx


fapp = FastAPI(title="Admin Microservice")


TELEGRAM_BOT_URL = "http://gs:8000"

@fapp.post("/account") 
async def get_accounts():
    
    


if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8003)