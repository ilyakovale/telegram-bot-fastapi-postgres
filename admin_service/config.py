import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
from pydantic import BaseModel

class GetAccountsMessageRequest(BaseModel):
    chat_id: int


BASE_DIR = Path(__file__).parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / '.env.db')
DB_URL = os.getenv("DB_URL")