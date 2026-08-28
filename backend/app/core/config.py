from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AlphaHunter"
    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://alphahunter:alphahunter@localhost:5432/alphahunter"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    upstox_client_id: str | None = None
    upstox_client_secret: str | None = None
    upstox_redirect_uri: str | None = None
    upstox_access_token: str | None = None
    upstox_refresh_token: str | None = None
    upstox_api_base_url: str = "https://api.upstox.com/v2"
    upstox_auth_dialog_url: str = "https://api.upstox.com/v2/login/authorization/dialog"
    upstox_token_url: str = "https://api.upstox.com/v2/login/authorization/token"
    upstox_instruments_url: str = (
        "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
    )
    upstox_suspended_instruments_url: str = (
        "https://assets.upstox.com/market-quote/instruments/exchange/suspended.json.gz"
    )
    upstox_oauth_state_ttl_seconds: int = 600
    upstox_http_max_retries: int = 3
    upstox_http_backoff_seconds: float = 1.0

    backtest_default_starting_capital: int = 1_000_000
    backtest_default_entry_slippage_bps: int = 5
    backtest_default_exit_slippage_bps: int = 5

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return ["http://localhost:3000"]

    @property
    def upstox_oauth_configured(self) -> bool:
        return bool(self.upstox_client_id and self.upstox_client_secret and self.upstox_redirect_uri)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
