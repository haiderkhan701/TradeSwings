from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"
    __table_args__ = (
        UniqueConstraint("instrument_key", name="uq_instruments_instrument_key"),
        UniqueConstraint("isin", name="uq_instruments_isin"),
        Index("ix_instruments_symbol_active", "trading_symbol", "active"),
        Index("ix_instruments_exchange_segment_type", "exchange", "segment", "instrument_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_key: Mapped[str] = mapped_column(String(128), nullable=False)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    segment: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument_type: Mapped[str] = mapped_column(String(32), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trading_symbol: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lot_size: Mapped[int] = mapped_column(Integer, nullable=False)
    freeze_quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    tick_size: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    qty_multiplier: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    security_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="upstox")
    source_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
