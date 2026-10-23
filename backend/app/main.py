import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.errors import register_error_handlers
from app.routers import debtors, payments, students


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="O'quv markazi to'lovlari",
    description="O'quvchilar, to'lovlar va qarzdorlarni hisobga olish API",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

register_error_handlers(app)

app.include_router(students.router)
app.include_router(payments.router)
app.include_router(debtors.router)


@app.get("/", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
