from pydantic import BaseModel


class UpstoxStatusResponse(BaseModel):
    provider: str
    configured: bool
    authenticated: bool
    token_available: bool
    token_source: str | None
    token_expiry: str | None


class UpstoxCallbackResponse(BaseModel):
    status: str
    provider: str
    authenticated: bool
    token_expiry: str | None
