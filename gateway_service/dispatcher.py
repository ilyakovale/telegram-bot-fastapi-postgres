import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from gateway_service.config import TOKEN
    from gateway_service.handlers.account import router_account
    from gateway_service.handlers.admin import router_admin
    from gateway_service.handlers.main import router_main
    from gateway_service.handlers.order import router_order
except (ImportError, ModuleNotFoundError):
    from config import TOKEN
    from handlers.account import router_account
    from handlers.admin import router_admin
    from handlers.main import router_main
    from handlers.order import router_order

bot = None
if TOKEN:
    try:
        bot = Bot(token=TOKEN)
    except Exception as e:
        logging.warning(f"Не удалось инициализировать бота: {e}")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


def create_storage():
    if (
        os.getenv("TESTING")
        or "PYTEST_CURRENT_TEST" in os.environ
        or "pytest" in os.getenv("_", "")
    ):
        return MemoryStorage()
    try:
        import redis
        from aiogram.fsm.storage.redis import RedisStorage

        client = redis.from_url(REDIS_URL, socket_connect_timeout=1)
        try:
            client.ping()
        finally:
            client.close()
        return RedisStorage.from_url(REDIS_URL)
    except Exception as e:
        logging.warning(f"Не удалось подключиться к Redis ({e}), используется MemoryStorage")
        return MemoryStorage()


storage = create_storage()
dp = Dispatcher(storage=storage)

dp.include_router(router_admin)
dp.include_router(router_account)
dp.include_router(router_order)
dp.include_router(router_main)
