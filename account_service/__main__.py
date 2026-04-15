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

BASE_DIR = Path(__file__).parent.parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / '.env.token')
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)
print (f"TOKEN: {TOKEN}")