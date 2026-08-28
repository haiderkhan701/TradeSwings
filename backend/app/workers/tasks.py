from app.db.session import SessionLocal
from app.providers.market_data.upstox import UpstoxProvider
from app.services.instrument_sync import InstrumentSyncService
from app.workers.celery_app import celery_app


@celery_app.task(name="upstox.sync_instruments")
def sync_upstox_instruments_task() -> dict[str, object]:
    db = SessionLocal()
    try:
        return InstrumentSyncService(db, UpstoxProvider()).sync_instruments().to_dict()
    finally:
        db.close()
