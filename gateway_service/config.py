import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / ".env.token")
TOKEN = os.getenv("TOKEN")
if not TOKEN and (
    os.getenv("TESTING") or "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules
):
    TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"

if not TOKEN:
    print(
        "Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.token."
    )
    exit(1)
print(f"TOKEN: {TOKEN}")

ADMINS_RAW = os.getenv("ADMINS", "")
ADMINS = (
    [int(admin.strip()) for admin in ADMINS_RAW.split(",") if admin.strip().isdigit()]
    if ADMINS_RAW
    else []
)
print(f"ADMINS: {ADMINS}")

contacts_path = BASE_DIR / "contacts.txt"
if contacts_path.exists():
    with open(contacts_path, "r", encoding="utf-8") as file:
        contacts = file.read().strip()
else:
    contacts = os.getenv("CONTACTS", "Контактная информация не указана.")

if not contacts:
    print("Ошибка: Не найден файл contacts.txt или он пустой.")
    exit(1)
print("contacts.txt успешно загружен.")

load_dotenv(BASE_DIR / ".env.url")

ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account_service:8001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8002")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

print(f"ACCOUNT_SERVICE_URL: {ACCOUNT_SERVICE_URL}")
print(f"ORDER_SERVICE_URL: {ORDER_SERVICE_URL}")
print(f"REDIS_URL: {REDIS_URL}")
