from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.instruments import (
    InstrumentListResponse,
    InstrumentResponse,
    InstrumentStatusResponse,
    InstrumentSummaryResponse,
)
from app.services.instruments import (
    count_active_nse_equities,
    get_instrument_by_symbol,
    latest_instrument_sync,
    list_instruments,
)

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=InstrumentListResponse)
def get_instruments(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    active: bool | None = True,
) -> dict[str, object]:
    items, total = list_instruments(db, page=page, page_size=page_size, active=active)
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/summary", response_model=InstrumentSummaryResponse)
def get_instrument_summary(db: DbSession) -> dict[str, object]:
    latest_sync = latest_instrument_sync(db)
    return {
        "total_nse_equities": count_active_nse_equities(db),
        "last_sync_timestamp": latest_sync.completed_at if latest_sync else None,
        "last_sync_status": latest_sync.status if latest_sync else None,
    }


@router.get("/{symbol}", response_model=InstrumentResponse)
def get_instrument(symbol: str, db: DbSession):
    instrument = get_instrument_by_symbol(db, symbol)
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument


@router.get("/{symbol}/status", response_model=InstrumentStatusResponse)
def get_instrument_status(symbol: str, db: DbSession) -> dict[str, object]:
    instrument = get_instrument_by_symbol(db, symbol)
    if instrument is None:
        return {"symbol": symbol.upper(), "found": False, "active": False}
    return {
        "symbol": instrument.trading_symbol,
        "found": True,
        "active": instrument.active,
        "instrument_key": instrument.instrument_key,
        "source": instrument.source,
        "source_date": instrument.source_date,
    }
