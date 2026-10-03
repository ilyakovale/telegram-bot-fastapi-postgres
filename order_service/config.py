import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent

load_dotenv(BASE_DIR / ".env.db")
load_dotenv(BASE_DIR.parent / ".env.db")
DB_URL = os.getenv(
    "DB_URL", "postgresql+asyncpg://postgres:1Is9Ts_bkf8&в@db:5432/telegram_bot"
)
