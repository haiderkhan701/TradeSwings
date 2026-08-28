from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_health import DataHealthRecord
from app.models.instrument import Instrument
from app.services.instrument_parser import (
    extract_suspended_instrument_keys,
    parse_upstox_nse_equity_instruments,
)

IST = ZoneInfo("Asia/Kolkata")


class InstrumentProvider(Protocol):
    def get_instruments(self) -> list[dict]:
        ...

    def get_suspended_instruments(self) -> list[dict]:
        ...


@dataclass(frozen=True)
class InstrumentSyncResult:
    status: str
    source: str
    total_records_downloaded: int
    nse_equity_records: int
    inserted: int
    updated: int
    deactivated: int
    rejected: int
    sync_timestamp: datetime

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "source": self.source,
            "total_records_downloaded": self.total_records_downloaded,
            "nse_equity_records": self.nse_equity_records,
            "inserted": self.inserted,
            "updated": self.updated,
            "deactivated": self.deactivated,
            "rejected": self.rejected,
            "sync_timestamp": self.sync_timestamp.isoformat(),
        }


class InstrumentSyncService:
    def __init__(self, db: Session, provider: InstrumentProvider) -> None:
        self._db = db
        self._provider = provider

    def sync_instruments(self) -> InstrumentSyncResult:
        started_at = datetime.now(IST)
        health = DataHealthRecord(
            source="upstox",
            check_name="instrument_sync",
            status="started",
            started_at=started_at,
        )
        self._db.add(health)
        self._db.commit()

        try:
            instrument_records = self._provider.get_instruments()
            suspended_records = self._provider.get_suspended_instruments()
            suspended_keys = extract_suspended_instrument_keys(suspended_records)
            parsed, rejected, nse_equity_records = parse_upstox_nse_equity_instruments(
                instrument_records,
                suspended_keys,
                source_date=started_at.date(),
            )

            parsed_keys = {instrument.instrument_key for instrument in parsed}
            existing = {
                instrument.instrument_key: instrument
                for instrument in self._db.scalars(
                    select(Instrument).where(Instrument.source == "upstox")
                ).all()
            }

            inserted = 0
            updated = 0
            for parsed_instrument in parsed:
                db_instrument = existing.get(parsed_instrument.instrument_key)
                values = parsed_instrument.model_values()
                if db_instrument is None:
                    self._db.add(Instrument(**values))
                    inserted += 1
                else:
                    for key, value in values.items():
                        setattr(db_instrument, key, value)
                    updated += 1

            deactivated = 0
            for instrument_key, db_instrument in existing.items():
                if db_instrument.active and instrument_key not in parsed_keys:
                    db_instrument.active = False
                    deactivated += 1

            completed_at = datetime.now(IST)
            result = InstrumentSyncResult(
                status="success",
                source="upstox",
                total_records_downloaded=len(instrument_records),
                nse_equity_records=nse_equity_records,
                inserted=inserted,
                updated=updated,
                deactivated=deactivated,
                rejected=len(rejected),
                sync_timestamp=completed_at,
            )

            health.status = "success"
            health.completed_at = completed_at
            health.source_timestamp = started_at
            health.total_records = len(instrument_records)
            health.accepted_records = len(parsed)
            health.rejected_records = len(rejected)
            health.details = {
                **result.to_dict(),
                "validation_failures": [failure.__dict__ for failure in rejected[:50]],
            }
            self._db.commit()
            return result
        except Exception as exc:
            health.status = "failed"
            health.completed_at = datetime.now(IST)
            health.error_message = exc.__class__.__name__
            self._db.commit()
            raise
