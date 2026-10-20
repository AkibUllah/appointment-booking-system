from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.booking_service import BookingService

DB = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


def require_admin(settings: Config, x_admin_token: Annotated[str | None, Header()] = None) -> None:
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="admin token required")


def booking_service(db: DB, settings: Config) -> BookingService:
    return BookingService(db, settings)


Service = Annotated[BookingService, Depends(booking_service)]
