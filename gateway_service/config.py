import os
import sys
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

BASE_DIR = Path(__file__).parent
print(f"Python ищет файлы в: {BASE_DIR}")

sys.path.append(str((BASE_DIR.parent) / 'requests_templates')) 

load_dotenv(BASE_DIR / '.env.token')
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)
print (f"TOKEN: {TOKEN}")

ADMINS = os.getenv("ADMINS")
ADMINS = [int(admin) for admin in ADMINS.split(",")] if ADMINS else []
print (f"ADMINS: {ADMINS}")

with open(BASE_DIR/ 'contacts.txt', 'r', encoding='utf-8') as file:
    contacts = file.read()

if not contacts:
    print("Ошибка: Не найден файл contacts.txt или он пустой. Убедитесь, что файл существует и содержит контактную информацию.")
    exit(1)
print("contacts.txt успешно загружен.")

ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL")
ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL")

if not ACCOUNT_SERVICE_URL:
    print("Ошибка: ACCOUNT_SERVICE_URL")
    exit(1)
print(f"ACCOUNT_SERVICE_URL: {ACCOUNT_SERVICE_URL}")

if not ORDER_SERVICE_URL:
    print("Ошибка: ORDER_SERVICE_URL")
    exit(1)
print(f"ORDER_SERVICE_URL: {ORDER_SERVICE_URL}")

if not ADMIN_SERVICE_URL:
    print("Ошибка: ADMIN_SERVICE_URL")
    exit(1)
print(f"ADMIN_SERVICE_URL: {ADMIN_SERVICE_URL}")
