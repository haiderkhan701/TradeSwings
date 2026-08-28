from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.models.upstox_auth import UpstoxToken
from app.providers.market_data.upstox import (
    UpstoxProvider,
    UpstoxRateLimitError,
    UpstoxUnauthorizedError,
    next_upstox_token_expiry,
    parse_token_response,
)
from app.services.oauth_state import OAuthStateService

IST = ZoneInfo("Asia/Kolkata")


def test_upstox_configuration_validation() -> None:
    configured = Settings(
        upstox_client_id="client-id",
        upstox_client_secret="client-secret",
        upstox_redirect_uri="http://localhost:8000/api/v1/upstox/auth/callback",
    )

    assert configured.upstox_oauth_configured is True
    assert Settings().upstox_oauth_configured is False


def test_oauth_state_generation_validation_and_reuse_rejection(db_session: Session) -> None:
    service = OAuthStateService(db_session)

    state = service.create_state()

    assert service.validate_state(state) is True
    assert service.validate_state(state) is False
    assert service.validate_state("wrong-state") is False


def test_token_exchange_response_parsing_without_expiry_uses_upstox_daily_expiry() -> None:
    token = parse_token_response({"access_token": "access-token", "token_type": "Bearer"})

    assert token.access_token == "access-token"
    assert token.expires_at is not None
    assert token.expires_at.tzinfo is not None


def test_next_upstox_expiry_rolls_to_next_330_am() -> None:
    expiry = next_upstox_token_expiry(datetime(2026, 8, 21, 4, 0, tzinfo=IST))

    assert expiry == datetime(2026, 8, 22, 3, 30, tzinfo=IST)


def test_unauthorized_token_exchange_raises_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid"})

    monkeypatch.setattr(settings, "upstox_client_id", "client-id")
    monkeypatch.setattr(settings, "upstox_client_secret", "client-secret")
    monkeypatch.setattr(settings, "upstox_redirect_uri", "http://callback")

    provider = UpstoxProvider(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(UpstoxUnauthorizedError):
        provider.exchange_authorization_code("single-use-code")


def test_rate_limit_retry_for_idempotent_download(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, content=b"rate limited")
        return httpx.Response(200, json=[])

    monkeypatch.setattr(settings, "upstox_http_max_retries", 1)
    provider = UpstoxProvider(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert provider.get_instruments() == []
    assert calls == 2


def test_rate_limit_exhaustion_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"}, content=b"rate limited")

    monkeypatch.setattr(settings, "upstox_http_max_retries", 1)
    provider = UpstoxProvider(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(UpstoxRateLimitError):
        provider.get_instruments()


def test_upstox_status_endpoint_does_not_return_token(client, db_session: Session) -> None:
    db_session.add(
        UpstoxToken(
            provider="upstox",
            access_token="secret-access-token",
            expires_at=datetime.now(IST) + timedelta(hours=1),
        )
    )
    db_session.commit()

    response = client.get("/api/v1/upstox/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["authenticated"] is True
    assert "secret-access-token" not in response.text
    assert "access_token" not in payload
