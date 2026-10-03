import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(Path.cwd() / ".env")
load_dotenv(Path.cwd() / ".env.token")
load_dotenv(Path.cwd() / "gateway_service" / ".env.token")
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR.parent / ".env.token")
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.token")

TOKEN = os.getenv("TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip().strip("'\"")

if not TOKEN:
    if os.getenv("TESTING") or "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
        TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
    else:
        print("Предупреждение: Не найден токен бота. Убедитесь, что переменная TOKEN установлена.")
print(f"TOKEN: {TOKEN}")

ADMINS_RAW = os.getenv("ADMINS", "")
if ADMINS_RAW:
    ADMINS_RAW = ADMINS_RAW.strip().strip("'\"")
ADMINS = (
    [int(admin.strip()) for admin in ADMINS_RAW.split(",") if admin.strip().isdigit()]
    if ADMINS_RAW
    else []
)
print(f"ADMINS: {ADMINS}")

contacts_path = BASE_DIR / "contacts.txt"
if not contacts_path.exists():
    contacts_path = BASE_DIR.parent / "contacts.txt"
if not contacts_path.exists():
    contacts_path = Path.cwd() / "contacts.txt"
if not contacts_path.exists():
    contacts_path = Path.cwd() / "gateway_service" / "contacts.txt"

if contacts_path.exists():
    with open(contacts_path, "r", encoding="utf-8") as file:
        contacts = file.read().strip()
else:
    contacts = os.getenv("CONTACTS", "Контактная информация не указана.")

if not contacts:
    contacts = "Контактная информация не указана."
print("contacts.txt успешно загружен.")

load_dotenv(Path.cwd() / ".env.url")
load_dotenv(Path.cwd() / "gateway_service" / ".env.url")
load_dotenv(BASE_DIR.parent / ".env.url")
load_dotenv(BASE_DIR / ".env.url")

ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account_service:8001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8002")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

print(f"ACCOUNT_SERVICE_URL: {ACCOUNT_SERVICE_URL}")
print(f"ORDER_SERVICE_URL: {ORDER_SERVICE_URL}")
print(f"REDIS_URL: {REDIS_URL}")
