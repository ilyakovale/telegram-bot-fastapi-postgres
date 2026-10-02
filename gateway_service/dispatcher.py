from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from handlers.account import router_account
from handlers.admin import router_admin
from handlers.main import router_main
from handlers.order import router_order

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(router_admin)
dp.include_router(router_account)
dp.include_router(router_order)
dp.include_router(router_main)
