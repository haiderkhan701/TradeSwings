from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.upstox_auth import UpstoxToken
from app.providers.market_data.upstox import UpstoxTokenResponse

IST = ZoneInfo("Asia/Kolkata")


class UpstoxTokenStore:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(self, token: UpstoxTokenResponse) -> UpstoxToken:
        existing = self._db.scalar(select(UpstoxToken).where(UpstoxToken.provider == "upstox"))
        if existing is None:
            existing = UpstoxToken(provider="upstox", access_token=token.access_token)
            self._db.add(existing)

        existing.access_token = token.access_token
        existing.refresh_token = token.refresh_token
        existing.token_type = token.token_type
        existing.expires_at = token.expires_at
        self._db.commit()
        self._db.refresh(existing)
        return existing

    def latest(self) -> UpstoxToken | None:
        return self._db.scalar(select(UpstoxToken).where(UpstoxToken.provider == "upstox"))


def build_safe_upstox_status(db: Session) -> dict[str, object]:
    stored = UpstoxTokenStore(db).latest()
    env_token_available = bool(settings.upstox_access_token)
    db_token_available = stored is not None and bool(stored.access_token)
    expires_at = _ensure_aware_ist(stored.expires_at) if stored and stored.expires_at else None
    expired = expires_at is not None and expires_at <= datetime.now(IST)

    return {
        "provider": "upstox",
        "configured": settings.upstox_oauth_configured,
        "authenticated": bool((env_token_available or db_token_available) and not expired),
        "token_available": bool(env_token_available or db_token_available),
        "token_source": "database" if db_token_available else "environment" if env_token_available else None,
        "token_expiry": expires_at.isoformat() if expires_at else None,
    }


def _ensure_aware_ist(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=IST)
    return value.astimezone(IST)
