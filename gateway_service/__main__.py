import asyncio

import uvicorn
from fastapi import FastAPI

try:
    from gateway_service.dispatcher import bot, dp
except (ImportError, ModuleNotFoundError):
    from dispatcher import bot, dp

fapp = FastAPI(title="Gateway Microservice")


@fapp.get("/health")
async def health():
    return {"status": "ok"}


async def run_fastapi():
    config = uvicorn.Config(fapp, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    print("🚀 FastAPI запущен на http://gateway_service:8000")
    if bot:
        print("Бот запущен...")
        await asyncio.gather(run_fastapi(), dp.start_polling(bot))
    else:
        print("⚠️ Бот не запущен (TOKEN не задан). Запущен только FastAPI.")
        await run_fastapi()


if __name__ == "__main__":
    asyncio.run(main())
