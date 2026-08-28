from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


@dataclass(frozen=True)
class ParsedInstrument:
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

    def model_values(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RejectedInstrument:
    instrument_key: str | None
    trading_symbol: str | None
    reason: str


def parse_upstox_nse_equity_instruments(
    records: list[dict[str, Any]],
    suspended_instrument_keys: set[str] | None = None,
    source_date: date | None = None,
) -> tuple[list[ParsedInstrument], list[RejectedInstrument], int]:
    suspended = suspended_instrument_keys or set()
    seen_keys: set[str] = set()
    seen_isins: set[str] = set()
    parsed: list[ParsedInstrument] = []
    rejected: list[RejectedInstrument] = []
    nse_equity_records = 0
    effective_source_date = source_date or datetime.now(IST).date()

    for record in records:
        if not _is_nse_eq_equity(record):
            continue
        nse_equity_records += 1

        instrument_key = _clean_str(record.get("instrument_key"))
        trading_symbol = _clean_str(record.get("trading_symbol"))

        if instrument_key in suspended:
            rejected.append(RejectedInstrument(instrument_key, trading_symbol, "suspended_instrument"))
            continue
        if not instrument_key:
            rejected.append(RejectedInstrument(None, trading_symbol, "missing_instrument_key"))
            continue
        if instrument_key in seen_keys:
            rejected.append(RejectedInstrument(instrument_key, trading_symbol, "duplicate_instrument_key"))
            continue
        if not trading_symbol:
            rejected.append(RejectedInstrument(instrument_key, None, "missing_trading_symbol"))
            continue

        isin = _clean_str(record.get("isin"))
        if not isin:
            rejected.append(RejectedInstrument(instrument_key, trading_symbol, "missing_isin"))
            continue
        if isin in seen_isins:
            rejected.append(RejectedInstrument(instrument_key, trading_symbol, "duplicate_isin"))
            continue

        try:
            lot_size = _positive_int(record.get("lot_size"), "lot_size")
            tick_size = _positive_decimal(record.get("tick_size"), "tick_size")
            freeze_quantity = _optional_decimal(record.get("freeze_quantity"), "freeze_quantity")
            qty_multiplier = _optional_decimal(record.get("qty_multiplier"), "qty_multiplier")
        except ValueError as exc:
            rejected.append(RejectedInstrument(instrument_key, trading_symbol, str(exc)))
            continue

        name = _clean_str(record.get("name"))
        if not name:
            rejected.append(RejectedInstrument(instrument_key, trading_symbol, "missing_name"))
            continue

        seen_keys.add(instrument_key)
        seen_isins.add(isin)
        parsed.append(
            ParsedInstrument(
                instrument_key=instrument_key,
                exchange="NSE",
                segment="NSE_EQ",
                instrument_type="EQ",
                isin=isin,
                trading_symbol=trading_symbol,
                name=name,
                short_name=_clean_str(record.get("short_name")),
                lot_size=lot_size,
                freeze_quantity=freeze_quantity,
                tick_size=tick_size,
                qty_multiplier=qty_multiplier,
                security_type=_clean_str(record.get("security_type")),
                active=True,
                source="upstox",
                source_date=effective_source_date,
            )
        )

    return parsed, rejected, nse_equity_records


def extract_suspended_instrument_keys(records: list[dict[str, Any]]) -> set[str]:
    return {
        instrument_key
        for record in records
        if (instrument_key := _clean_str(record.get("instrument_key")))
    }


def _is_nse_eq_equity(record: dict[str, Any]) -> bool:
    return (
        record.get("exchange") == "NSE"
        and record.get("segment") == "NSE_EQ"
        and record.get("instrument_type") == "EQ"
    )


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field_name}") from exc
    if parsed <= 0:
        raise ValueError(f"invalid_{field_name}")
    return parsed


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    parsed = _optional_decimal(value, field_name)
    if parsed is None or parsed <= 0:
        raise ValueError(f"invalid_{field_name}")
    return parsed


def _optional_decimal(value: Any, field_name: str) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid_{field_name}") from exc
    return parsed
