import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


class AccountID(BaseModel):
    chat_id: int


class GetAccountMessageRequest(BaseModel):
    chat_id: int
    command: str = ""


class SetAccountMessageRequest(BaseModel):
    chat_id: int
    command: str = ""
    name: str
    address: str
    phone_number: str


BASE_DIR = Path(__file__).parent

load_dotenv(BASE_DIR / ".env.db")
DB_URL = os.getenv("DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
