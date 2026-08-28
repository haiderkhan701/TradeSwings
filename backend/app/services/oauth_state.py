import hashlib
import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.upstox_auth import UpstoxOAuthState

IST = ZoneInfo("Asia/Kolkata")


def hash_oauth_state(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


class OAuthStateService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_state(self) -> str:
        state = secrets.token_urlsafe(32)
        now = datetime.now(IST)
        self._db.add(
            UpstoxOAuthState(
                state_hash=hash_oauth_state(state),
                expires_at=now + timedelta(seconds=settings.upstox_oauth_state_ttl_seconds),
            )
        )
        self._db.commit()
        return state

    def validate_state(self, state: str) -> bool:
        state_hash = hash_oauth_state(state)
        record = self._db.scalar(
            select(UpstoxOAuthState).where(UpstoxOAuthState.state_hash == state_hash)
        )
        now = datetime.now(IST)
        if record is None:
            return False
        expires_at = _ensure_aware_ist(record.expires_at)
        if record.consumed_at is not None or expires_at <= now:
            return False
        record.consumed_at = now
        self._db.commit()
        return True


def _ensure_aware_ist(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=IST)
    return value.astimezone(IST)
