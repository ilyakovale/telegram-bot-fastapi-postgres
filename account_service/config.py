import os
import sys
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
from pydantic import BaseModel

class GetAccountMessageRequest(BaseModel):
    chat_id: int
    command: str     

class SetAccountMessageRequest(BaseModel):
    chat_id: int
    command: str    
    name: str
    address: str
    phone_number: str


BASE_DIR = Path(__file__).parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / '.env.db')
DB_URL = os.getenv("DB_URL")