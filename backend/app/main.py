"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, public
from app.api.schemas import ErrorOut
from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.logging import configure_logging
from app.db.models import Base
from app.db.session import engine
from app.services.scheduler import build_scheduler

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    Base.metadata.create_all(bind=engine)
    scheduler = None
    if settings.scheduler_enabled:
        scheduler = build_scheduler(settings)
        scheduler.start()
        log.info("reminder scheduler started (every %ss)", settings.reminder_interval_seconds)
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Doctor chamber appointment booking for Dhaka: slots, bookings, reminders.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorOut(code=exc.code, message=exc.message).model_dump(),
    )


@app.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "ok", "service": "appointment-booking", "timezone": settings.clinic_timezone}


app.include_router(public.router)
app.include_router(admin.router)
