from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.providers.market_data.upstox import (
    UpstoxConfigError,
    UpstoxProvider,
    UpstoxProviderError,
)
from app.schemas.instruments import InstrumentSyncResponse
from app.schemas.upstox import UpstoxCallbackResponse, UpstoxStatusResponse
from app.services.instrument_sync import InstrumentSyncService
from app.services.oauth_state import OAuthStateService
from app.services.upstox_auth import UpstoxTokenStore, build_safe_upstox_status

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
RequiredQuery = Annotated[str, Query(min_length=1)]


@router.get("/auth/login")
def upstox_auth_login(db: DbSession) -> RedirectResponse:
    state = OAuthStateService(db).create_state()
    try:
        login_url = UpstoxProvider().build_login_url(state)
    except UpstoxConfigError as exc:
        raise HTTPException(status_code=503, detail="Upstox OAuth is not configured") from exc
    return RedirectResponse(login_url, status_code=307)


@router.get("/auth/callback", response_model=UpstoxCallbackResponse)
def upstox_auth_callback(
    db: DbSession,
    code: RequiredQuery,
    state: RequiredQuery,
) -> dict[str, object]:
    if not OAuthStateService(db).validate_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    try:
        token = UpstoxProvider().exchange_authorization_code(code)
    except UpstoxConfigError as exc:
        raise HTTPException(status_code=503, detail="Upstox OAuth is not configured") from exc
    except UpstoxProviderError as exc:
        raise HTTPException(status_code=502, detail="Upstox authentication failed") from exc

    stored = UpstoxTokenStore(db).save(token)
    return {
        "status": "success",
        "provider": "upstox",
        "authenticated": True,
        "token_expiry": stored.expires_at.isoformat() if stored.expires_at else None,
    }


@router.get("/status", response_model=UpstoxStatusResponse)
def upstox_status(db: DbSession) -> dict[str, object]:
    return build_safe_upstox_status(db)


@router.post("/instruments/sync", response_model=InstrumentSyncResponse)
def sync_upstox_instruments(db: DbSession) -> dict[str, object]:
    try:
        result = InstrumentSyncService(db, UpstoxProvider()).sync_instruments()
    except UpstoxProviderError as exc:
        raise HTTPException(status_code=502, detail="Upstox instrument synchronization failed") from exc
    return result.to_dict()
