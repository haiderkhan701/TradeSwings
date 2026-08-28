import gzip
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import httpx
import structlog
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.providers.market_data.base import MarketDataProvider

IST = ZoneInfo("Asia/Kolkata")
logger = structlog.get_logger(__name__)


class UpstoxProviderError(RuntimeError):
    pass


class UpstoxUnauthorizedError(UpstoxProviderError):
    pass


class UpstoxConfigError(UpstoxProviderError):
    pass


class UpstoxRateLimitError(UpstoxProviderError):
    pass


class UpstoxTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = Field(default=None, ge=0)
    expires_at: datetime | None = None


@dataclass(frozen=True)
class StoredToken:
    access_token: str
    expires_at: datetime | None = None


def next_upstox_token_expiry(now: datetime | None = None) -> datetime:
    current = now.astimezone(IST) if now else datetime.now(IST)
    expiry = current.replace(hour=3, minute=30, second=0, microsecond=0)
    if current >= expiry:
        expiry = expiry + timedelta(days=1)
    return expiry


def parse_token_response(payload: dict[str, Any]) -> UpstoxTokenResponse:
    try:
        token = UpstoxTokenResponse.model_validate(payload)
    except ValidationError as exc:
        raise UpstoxProviderError("Upstox token response validation failed") from exc

    if token.expires_at is None and token.expires_in is not None:
        token.expires_at = datetime.now(IST) + timedelta(seconds=token.expires_in)
    if token.expires_at is None:
        token.expires_at = next_upstox_token_expiry()
    return token


class UpstoxProvider(MarketDataProvider):
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        access_token: str | None = None,
    ) -> None:
        self._http = http_client or httpx.Client(timeout=30.0, follow_redirects=True)
        self._access_token = access_token

    def build_login_url(self, state: str) -> str:
        if not settings.upstox_client_id or not settings.upstox_redirect_uri:
            raise UpstoxConfigError("Upstox OAuth configuration is incomplete")

        query = urlencode(
            {
                "response_type": "code",
                "client_id": settings.upstox_client_id,
                "redirect_uri": settings.upstox_redirect_uri,
                "state": state,
            }
        )
        return f"{settings.upstox_auth_dialog_url}?{query}"

    def exchange_authorization_code(self, code: str) -> UpstoxTokenResponse:
        if not settings.upstox_oauth_configured:
            raise UpstoxConfigError("Upstox OAuth configuration is incomplete")

        response = self._request(
            "POST",
            settings.upstox_token_url,
            retry_on_rate_limit=False,
            headers={
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "code": code,
                "client_id": settings.upstox_client_id,
                "client_secret": settings.upstox_client_secret,
                "redirect_uri": settings.upstox_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if response.status_code in {401, 403}:
            raise UpstoxUnauthorizedError("Upstox authorization failed")
        if response.is_error:
            raise UpstoxProviderError(f"Upstox token exchange failed with HTTP {response.status_code}")

        return parse_token_response(response.json())

    def get_instruments(self) -> list[dict[str, Any]]:
        return self._download_json_gzip(settings.upstox_instruments_url)

    def get_suspended_instruments(self) -> list[dict[str, Any]]:
        return self._download_json_gzip(settings.upstox_suspended_instruments_url)

    def get_historical_candles(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raise NotImplementedError("Historical data ingestion is Milestone 3 scope")

    def get_quote(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("Quote retrieval is not part of Milestone 2")

    def subscribe_market_feed(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Market feed streaming is not part of Milestone 2")

    def get_market_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("Generic market data retrieval is not part of Milestone 2")

    def _download_json_gzip(self, url: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            url,
            retry_on_rate_limit=True,
            headers={"Accept": "application/json"},
        )
        if response.status_code in {401, 403}:
            raise UpstoxUnauthorizedError("Upstox instrument download was unauthorized")
        if response.is_error:
            raise UpstoxProviderError(f"Upstox instrument download failed with HTTP {response.status_code}")

        content = response.content
        if url.endswith(".gz"):
            try:
                content = gzip.decompress(content)
            except OSError:
                pass

        parsed = json.loads(content.decode("utf-8"))
        if not isinstance(parsed, list):
            raise UpstoxProviderError("Upstox instrument response was not a JSON list")
        return parsed

    def _request(
        self,
        method: str,
        url: str,
        *,
        retry_on_rate_limit: bool,
        **kwargs: Any,
    ) -> httpx.Response:
        attempts = max(1, settings.upstox_http_max_retries + 1)
        for attempt in range(1, attempts + 1):
            response = self._http.request(method, url, **kwargs)
            if response.status_code != 429:
                return response

            if not retry_on_rate_limit:
                raise UpstoxRateLimitError("Upstox rate limit hit on non-retryable request")

            if attempt >= attempts:
                raise UpstoxRateLimitError("Upstox rate limit retries exhausted")

            retry_after = _retry_after_seconds(response.headers.get("Retry-After"))
            delay = retry_after if retry_after is not None else _bounded_backoff(attempt)
            logger.warning(
                "upstox_rate_limit_retry",
                method=method,
                attempt=attempt,
                retry_after_seconds=delay,
            )
            time.sleep(delay)

        raise UpstoxRateLimitError("Upstox rate limit retries exhausted")


def _bounded_backoff(attempt: int) -> float:
    delay = settings.upstox_http_backoff_seconds * (2 ** max(0, attempt - 1))
    return min(delay, 30.0)


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=IST)
    return max(0.0, (retry_at - datetime.now(retry_at.tzinfo)).total_seconds())
