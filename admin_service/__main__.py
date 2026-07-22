import asyncio
import uvicorn
from fastapi import FastAPI
from database import engine, Base

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 
    yield

fapp = FastAPI(title="Admin Microservice", lifespan=lifespan)

    

if __name__ == "__main__":
    uvicorn.run(fapp, host="0.0.0.0", port=8003)