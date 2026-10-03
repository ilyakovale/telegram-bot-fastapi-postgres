import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn
from fastapi import FastAPI

try:
    from dispatcher import bot, dp
except (ImportError, ModuleNotFoundError):
    from gateway_service.dispatcher import bot, dp

fapp = FastAPI(title="Gateway Microservice")


@fapp.get("/health")
async def health():
    return {"status": "ok"}


async def run_fastapi():
    config = uvicorn.Config(fapp, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    print("[FastAPI] Запущен на http://gateway_service:8000")
    if bot:
        print("[Bot] Бот запущен...")
        await asyncio.gather(run_fastapi(), dp.start_polling(bot))
    else:
        print("[Bot] Предупреждение: Бот не запущен (TOKEN не задан). Запущен только FastAPI.")
        await run_fastapi()


if __name__ == "__main__":
    asyncio.run(main())
