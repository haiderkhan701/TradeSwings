# AlphaHunter

AlphaHunter is a single-user, read-only NSE swing-trading research and stock-scanning platform.

Current status: Milestone 2 implements Upstox OAuth plumbing, the Upstox market-data provider shell, NSE equity instrument synchronization, PostgreSQL persistence, read-only verification APIs, and a simple verification UI.

Automatic trading/order placement is not implemented.

Strategy, indicators, backtesting and real-time scanner are not yet implemented.

## Architecture

AlphaHunter uses a monorepo:

```text
backend/   FastAPI, SQLAlchemy, Alembic, Celery, Upstox provider
frontend/  Next.js, TypeScript, verification UI
docs/      strategy, data, backtest, architecture, data-source docs
infra/     local infrastructure notes
tests/     cross-project test notes
```

Local services:

- PostgreSQL for persistence
- Redis for Celery and future short-lived state
- FastAPI backend on `http://localhost:8000`
- Next.js frontend on `http://localhost:3000`

## Local Environment

Copy the example file and keep the real file local:

```bash
cp .env.example .env
```

Never commit `.env`. It is ignored by Git.

Important variables:

```text
DATABASE_URL=postgresql+psycopg://alphahunter:alphahunter@postgres:5432/alphahunter
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

UPSTOX_CLIENT_ID=
UPSTOX_CLIENT_SECRET=
UPSTOX_REDIRECT_URI=http://localhost:8000/api/v1/upstox/auth/callback
```

The frontend must never contain `UPSTOX_CLIENT_SECRET`, access tokens, or refresh tokens.

## Start Services

Docker Compose path:

```bash
docker compose up --build
```

Manual backend path:

```bash
cd backend
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

Manual frontend path:

```bash
cd frontend
npm install
npm run dev
```

## Database Migrations

After PostgreSQL is running:

```bash
cd backend
alembic upgrade head
```

Milestone 2 migration creates:

- `instruments`
- `upstox_oauth_states`
- `upstox_tokens`
- `data_health`

## Upstox Manual Setup

Do not paste secrets into GitHub, Codex chat, or this conversation.

1. Open your Upstox Developer account.
2. Create or open the AlphaHunter developer application.
3. Copy the API key / Client ID.
4. Copy the API secret / Client Secret.
5. Configure the app redirect URI exactly as:

   ```text
   http://localhost:8000/api/v1/upstox/auth/callback
   ```

6. Put the values into your local `.env`:

   ```text
   UPSTOX_CLIENT_ID=your-client-id
   UPSTOX_CLIENT_SECRET=your-client-secret
   UPSTOX_REDIRECT_URI=http://localhost:8000/api/v1/upstox/auth/callback
   ```

7. Start AlphaHunter.
8. Open:

   ```text
   http://localhost:8000/api/v1/upstox/auth/login
   ```

9. Complete authorization on Upstox.
10. Upstox redirects back to AlphaHunter.
11. Verify safe authentication status:

   ```text
   http://localhost:8000/api/v1/upstox/status
   ```

The status endpoint reports only safe metadata. It does not return tokens.

## Synchronize NSE Equity Instruments

After migrations and app startup, run:

```bash
curl -X POST http://localhost:8000/api/v1/upstox/instruments/sync
```

This downloads the official Upstox NSE BOD instrument JSON, filters `exchange=NSE`, `segment=NSE_EQ`, `instrument_type=EQ`, rejects malformed records, upserts into PostgreSQL, marks missing existing instruments inactive, and writes data-health metadata.

Running sync twice should not create duplicate instruments.

## Verify Instruments

API:

```text
GET http://localhost:8000/api/v1/instruments?page=1&page_size=50
GET http://localhost:8000/api/v1/instruments/RELIANCE
GET http://localhost:8000/api/v1/instruments/RELIANCE/status
GET http://localhost:8000/api/v1/instruments/summary
```

Frontend:

```text
http://localhost:3000
```

The current UI shows Upstox connection status, total NSE equities, last synchronization timestamp, and a paginated instrument table.

## Tests

Backend:

```bash
cd backend
python -m pytest
python -m ruff check .
```

Frontend:

```bash
cd frontend
npm test
npm run build
npm audit
```

If `npm audit` cannot reach the registry because of network restrictions, treat that as an environment limitation, not an application test failure.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/STRATEGY_V1_1.md`
- `docs/DATA_SPEC_V1.md`
- `docs/DATA_SOURCE_MATRIX_V1.md`
- `docs/BACKTEST_SPEC_V1.md`
- `docs/CODEX_RULES.md`

`docs/STRATEGY_V1_1.md` is authoritative for strategy behavior. If implementation ambiguity appears later, stop and ask for clarification instead of inventing a rule.
