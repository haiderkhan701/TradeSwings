from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.services.instrument_parser import parse_upstox_nse_equity_instruments
from app.services.instrument_sync import InstrumentSyncService

IST = ZoneInfo("Asia/Kolkata")


def valid_record(
    *,
    key: str = "NSE_EQ|INE002A01018",
    isin: str = "INE002A01018",
    symbol: str = "RELIANCE",
) -> dict[str, object]:
    return {
        "segment": "NSE_EQ",
        "name": "RELIANCE INDUSTRIES LTD",
        "exchange": "NSE",
        "isin": isin,
        "instrument_type": "EQ",
        "instrument_key": key,
        "lot_size": 1,
        "freeze_quantity": 100000.0,
        "tick_size": 5.0,
        "trading_symbol": symbol,
        "short_name": "Reliance Industries",
        "security_type": "NORMAL",
        "qty_multiplier": 1.0,
    }


class FakeProvider:
    def __init__(self, records: list[dict], suspended: list[dict] | None = None) -> None:
        self.records = records
        self.suspended = suspended or []

    def get_instruments(self) -> list[dict]:
        return self.records

    def get_suspended_instruments(self) -> list[dict]:
        return self.suspended


def test_instrument_parser_filters_nse_eq_equity_only() -> None:
    records = [
        valid_record(),
        {**valid_record(key="NSE_FO|1", isin="FUTISIN", symbol="FUT"), "segment": "NSE_FO"},
        {**valid_record(key="BSE_EQ|1", isin="BSEISIN", symbol="BSE"), "exchange": "BSE"},
    ]

    parsed, rejected, nse_equity_records = parse_upstox_nse_equity_instruments(records)

    assert len(parsed) == 1
    assert rejected == []
    assert nse_equity_records == 1
    assert parsed[0].trading_symbol == "RELIANCE"


def test_instrument_parser_rejects_malformed_and_duplicates() -> None:
    duplicate = valid_record()
    missing_symbol = valid_record(key="NSE_EQ|INE111111111", isin="INE111111111", symbol="")
    bad_tick = {**valid_record(key="NSE_EQ|INE222222222", isin="INE222222222"), "tick_size": 0}

    parsed, rejected, _ = parse_upstox_nse_equity_instruments(
        [duplicate, duplicate, missing_symbol, bad_tick]
    )

    assert len(parsed) == 1
    assert [item.reason for item in rejected] == [
        "duplicate_instrument_key",
        "missing_trading_symbol",
        "invalid_tick_size",
    ]


def test_instrument_parser_rejects_suspended_records() -> None:
    parsed, rejected, _ = parse_upstox_nse_equity_instruments(
        [valid_record()],
        suspended_instrument_keys={"NSE_EQ|INE002A01018"},
    )

    assert parsed == []
    assert rejected[0].reason == "suspended_instrument"


def test_instrument_sync_is_idempotent_and_deactivates_missing_records(db_session: Session) -> None:
    first_provider = FakeProvider(
        [
            valid_record(),
            valid_record(key="NSE_EQ|INE009A01021", isin="INE009A01021", symbol="INFY"),
        ]
    )
    first_result = InstrumentSyncService(db_session, first_provider).sync_instruments()
    second_result = InstrumentSyncService(db_session, first_provider).sync_instruments()

    assert first_result.inserted == 2
    assert second_result.inserted == 0
    assert second_result.updated == 2
    assert db_session.query(Instrument).count() == 2

    smaller_provider = FakeProvider([valid_record()])
    third_result = InstrumentSyncService(db_session, smaller_provider).sync_instruments()

    assert third_result.deactivated == 1
    inactive = db_session.query(Instrument).filter_by(trading_symbol="INFY").one()
    assert inactive.active is False


def test_instrument_sync_persists_expected_values(db_session: Session) -> None:
    result = InstrumentSyncService(db_session, FakeProvider([valid_record()])).sync_instruments()
    stored = db_session.query(Instrument).one()

    assert result.status == "success"
    assert stored.instrument_key == "NSE_EQ|INE002A01018"
    assert stored.exchange == "NSE"
    assert stored.segment == "NSE_EQ"
    assert stored.instrument_type == "EQ"
    assert stored.tick_size == Decimal("5.0000")
    assert stored.source_date == datetime.now(IST).date()


def test_instruments_pagination_endpoint(client, db_session: Session) -> None:
    for index in range(3):
        db_session.add(
            Instrument(
                instrument_key=f"NSE_EQ|INE00000000{index}",
                exchange="NSE",
                segment="NSE_EQ",
                instrument_type="EQ",
                isin=f"INE00000000{index}",
                trading_symbol=f"SYM{index}",
                name=f"Company {index}",
                lot_size=1,
                tick_size=Decimal("5.0"),
                active=True,
                source="upstox",
                source_date=datetime.now(IST).date(),
            )
        )
    db_session.commit()

    response = client.get("/api/v1/instruments?page=1&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["items"]) == 2


def test_instrument_status_endpoint(client, db_session: Session) -> None:
    db_session.add(
        Instrument(
            instrument_key="NSE_EQ|INE002A01018",
            exchange="NSE",
            segment="NSE_EQ",
            instrument_type="EQ",
            isin="INE002A01018",
            trading_symbol="RELIANCE",
            name="Reliance Industries",
            lot_size=1,
            tick_size=Decimal("5.0"),
            active=True,
            source="upstox",
            source_date=datetime.now(IST).date(),
        )
    )
    db_session.commit()

    response = client.get("/api/v1/instruments/reliance/status")

    assert response.status_code == 200
    assert response.json()["active"] is True
