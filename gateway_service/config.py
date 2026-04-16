import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
print(f"Python ищет файлы в: {BASE_DIR}")

load_dotenv(BASE_DIR / '.env.token')
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Ошибка: Не найден токен бота. Убедитесь, что переменная TOKEN установлена в файле .env.")
    exit(1)
print (f"TOKEN: {TOKEN}")

ADMINS = os.getenv("ADMINS")
ADMINS = [int(admin) for admin in ADMINS.split(",")] if ADMINS else []
print (f"ADMINS: {ADMINS}")

with open(BASE_DIR / 'contacts.txt', 'r', encoding='utf-8') as file:
    contacts = file.read()

if not contacts:
    print("Ошибка: Не найден файл contacts.txt или он пустой. Убедитесь, что файл существует и содержит контактную информацию.")
    exit(1)
print("contacts.txt успешно загружен.")