import asyncio
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv, dotenv_values
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

fapp = FastAPI(title="Account Microservice")

BASE_DIR = Path(__file__).parent.parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / '.env.token')
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)
print (f"TOKEN: {TOKEN}")


class SendMessageRequest(BaseModel):
    chat_id: int
    text: str
    parse_mode: str = "HTML"

TELEGRAM_BOT_URL = "http://localhost:8000"

@fapp.post("/get_account")  # ← Бот отправляет сюда
async def get_account(request: SendMessageRequest):
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