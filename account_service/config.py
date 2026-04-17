import os
import sys
from dotenv import load_dotenv, dotenv_values
from pathlib import Path

BASE_DIR = Path(__file__).parent
print(f"Python ищет файлы в: {BASE_DIR}")

sys.path.append(str((BASE_DIR.parent) / 'requests_templates')) 
try:
    from accountrequests import AccountMessageRequest
except ImportError as e:
    print(f"Ошибка при импорте accountrequests: {e}")
    AccountMessageRequest = None