from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instrument_key: str
    exchange: str
    segment: str
    instrument_type: str
    isin: str | None
    trading_symbol: str
    name: str
    short_name: str | None
    lot_size: int
    freeze_quantity: Decimal | None
    tick_size: Decimal
    qty_multiplier: Decimal | None
    security_type: str | None
    active: bool
    source: str
    source_date: date
    created_at: datetime
    updated_at: datetime


class InstrumentListResponse(BaseModel):
    items: list[InstrumentResponse]
    page: int
    page_size: int
    total: int


class InstrumentStatusResponse(BaseModel):
    symbol: str
    found: bool
    active: bool
    instrument_key: str | None = None
    source: str | None = None
    source_date: date | None = None


class InstrumentSyncResponse(BaseModel):
    status: str
    source: str
    total_records_downloaded: int
    nse_equity_records: int
    inserted: int
    updated: int
    deactivated: int
    rejected: int
    sync_timestamp: datetime


class InstrumentSummaryResponse(BaseModel):
    total_nse_equities: int = Field(ge=0)
    last_sync_timestamp: datetime | None
    last_sync_status: str | None
