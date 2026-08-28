from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.data_health import DataHealthRecord
from app.models.instrument import Instrument


def list_instruments(
    db: Session,
    page: int,
    page_size: int,
    active: bool | None = True,
) -> tuple[list[Instrument], int]:
    statement = select(Instrument)
    count_statement = select(func.count()).select_from(Instrument)
    if active is not None:
        statement = statement.where(Instrument.active.is_(active))
        count_statement = count_statement.where(Instrument.active.is_(active))

    total = db.scalar(count_statement) or 0
    rows = db.scalars(
        statement.order_by(Instrument.trading_symbol)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return rows, total


def get_instrument_by_symbol(db: Session, symbol: str) -> Instrument | None:
    return db.scalar(
        select(Instrument).where(func.upper(Instrument.trading_symbol) == symbol.upper())
    )


def count_active_nse_equities(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Instrument)
            .where(
                Instrument.active.is_(True),
                Instrument.exchange == "NSE",
                Instrument.segment == "NSE_EQ",
                Instrument.instrument_type == "EQ",
            )
        )
        or 0
    )


def latest_instrument_sync(db: Session) -> DataHealthRecord | None:
    return db.scalar(
        select(DataHealthRecord)
        .where(
            DataHealthRecord.source == "upstox",
            DataHealthRecord.check_name == "instrument_sync",
        )
        .order_by(DataHealthRecord.started_at.desc())
        .limit(1)
    )
