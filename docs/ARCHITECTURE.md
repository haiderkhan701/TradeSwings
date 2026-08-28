# AlphaHunter Architecture

AlphaHunter is a single-user, read-only NSE swing-trading research and scanning platform.

V1 focuses on market-data ingestion, indicator calculation, deterministic Strategy V1.1 evaluation, historical backtesting, and a research dashboard. Real-time scanning and alerts come after backtesting is complete.

## Product Boundaries

V1 includes:

- Web-based research dashboard
- Backend services
- Upstox market-data integration
- NSE instrument synchronization
- Historical OHLCV ingestion
- Indicator engine
- Deterministic strategy engine
- Backtesting engine
- Performance analytics
- Historical and backtest result display

V1 excludes:

- Automatic order placement
- Live trading execution
- Broker order management
- Options trading
- Futures trading

The architecture may leave room for future execution modules, but V1 must remain read-only.

## Technology Stack

Backend:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

Database:

- PostgreSQL

Caching and real-time state:

- Redis

Background processing:

- Celery with Redis

Frontend:

- Next.js
- TypeScript
- Tailwind CSS

Charts:

- TradingView Lightweight Charts or another suitable financial charting library

Infrastructure:

- Docker
- Docker Compose

Testing:

- pytest for Python
- Frontend tests appropriate for the selected Next.js setup

## Proposed Folder Structure

```text
AlphaHunter/
  README.md
  .env.example
  docker-compose.yml
  docs/
    ARCHITECTURE.md
    BACKTEST_SPEC_V1.md
    CODEX_RULES.md
    DATA_SPEC_V1.md
    DATA_SOURCE_MATRIX_V1.md
    STRATEGY_V1_1.md
  backend/
    app/
      api/
        routes/
      core/
        config.py
        logging.py
        security.py
      db/
        base.py
        session.py
      models/
      schemas/
      providers/
        market_data/
          base.py
          upstox.py
      services/
        instruments/
        market_data/
        indicators/
        strategy/
        backtesting/
        analytics/
        data_health/
      workers/
      main.py
    alembic/
    tests/
    pyproject.toml
  frontend/
    app/
    components/
    lib/
    tests/
    package.json
  infra/
    README.md
  tests/
    README.md
```

This monorepo structure is confirmed for V1.

## Service Architecture

### Backend API

FastAPI exposes read-only endpoints for:

- System health
- Instrument search and universe inspection
- Historical candles
- Technical indicators
- Strategy candidates and signals
- Backtest runs
- Backtest metrics
- Dashboard data

V1 API routes must not expose order placement or broker trading actions.

### Background Workers

Workers handle long-running and scheduled tasks:

- Instrument synchronization
- Historical daily data ingestion
- Historical intraday data ingestion
- Data validation
- Indicator calculation
- Relative strength calculation
- Backtest execution
- Scheduled data-health checks
- Future real-time scanner tasks

V1 must not introduce Kubernetes or other complex orchestration.

### Database

PostgreSQL stores:

- Instruments
- Raw and derived market data
- Indicator values
- Strategy parameters
- Signals
- Backtest runs
- Backtest trades
- Metrics
- Data-health records

### Redis

Redis supports:

- Background job broker
- Celery result backend
- Future real-time scanner state
- Short-lived cache where appropriate

### Frontend

Next.js provides the research dashboard:

- Universe view
- Instrument detail page
- Candle chart
- Indicator overlays
- Strategy candidate list
- Signal explanation view
- Backtest run list
- Backtest metrics and breakdowns

## Market Data Provider Abstraction

Strategy and backtesting code must depend on an internal provider interface, not on Upstox directly.

Conceptual interface:

```text
MarketDataProvider
  get_instruments()
  get_historical_candles()
  get_quote()
  subscribe_market_feed()
  get_market_data()
```

Initial implementation:

```text
UpstoxProvider
```

Provider responsibilities:

- Authenticate with Upstox
- Normalize Upstox instrument data
- Normalize candle data
- Normalize quotes
- Normalize WebSocket feed messages later
- Return internal domain objects
- Preserve provider metadata for auditing

Provider non-responsibilities:

- Strategy decisions
- Indicator calculations
- Backtest execution
- Signal scoring

## Upstox Integration Approach

Implementation must use the current official Upstox API documentation.

Planned integration phases:

1. OAuth configuration and token handling
2. NSE equity instrument synchronization
3. Daily historical candle ingestion
4. Intraday 1-minute historical ingestion where available
5. Quote retrieval
6. WebSocket market feed for real-time scanning later

Initial field availability is tracked in `docs/DATA_SOURCE_MATRIX_V1.md`. Fields not available through Upstox must be marked as unavailable or secondary-source required. Do not implement a paid external provider until Upstox availability has been verified in code.

Secrets:

- Store client ID, client secret, redirect URI, and tokens outside source code.
- Use environment variables and local `.env`.
- Provide `.env.example` with placeholders.
- Never log secrets or tokens.

## Database Schema

Initial logical schema:

### `instruments`

- Internal instrument ID
- Provider instrument key
- Exchange
- Segment
- Symbol
- Trading symbol
- Name
- ISIN
- Sector
- Industry
- Tick size
- Lot size
- Listing status
- SME flag
- Active flag
- Provider metadata
- Created timestamp
- Updated timestamp

Indexes:

- Symbol
- Trading symbol
- Provider instrument key
- Exchange and segment

### `daily_candles`

- Instrument ID
- Trade date
- Open
- High
- Low
- Close
- Volume
- Traded value
- Open interest, where available
- Data source
- Adjustment status
- Ingested timestamp

Indexes:

- Instrument ID and trade date
- Trade date

### `intraday_candles`

- Instrument ID
- Timestamp
- Timeframe
- Open
- High
- Low
- Close
- Volume
- Traded value
- Open interest, where available
- Data source
- Ingested timestamp

Indexes:

- Instrument ID, timeframe, timestamp
- Timestamp

### `technical_daily`

- Instrument ID
- Trade date
- EMA20
- EMA50
- SMA50
- SMA200
- RSI14
- ATR14
- ATR percentage
- RVOL
- 10-day high
- 20-day high
- 50-day high
- 100-day high
- 252-day high
- Support level
- Resistance level

Indexes:

- Instrument ID and trade date

### `market_indices`

- Index symbol
- Trade date
- OHLCV values
- EMA/SMA values
- Market breadth fields
- Regime score
- Regime classification

Indexes:

- Index symbol and trade date

### `sector_indices`

- Sector index symbol
- Trade date
- OHLCV values
- EMA/SMA values
- RS5
- RS20
- Sector score

Indexes:

- Sector index symbol and trade date

### `relative_strength`

- Instrument ID
- Trade date
- Benchmark symbol
- Sector index symbol
- RS5
- RS20
- RS60
- Sector RS20
- Stock versus sector RS20

Indexes:

- Instrument ID and trade date

### `fundamentals`

- Instrument ID
- As-of date
- Revenue trend
- Earnings trend
- Profitability fields
- Debt fields
- Promoter pledge
- Red flag status
- Source
- Availability status

Indexes:

- Instrument ID and as-of date

### `ownership`

- Instrument ID
- As-of date
- Promoter holding
- Institutional holding
- Public holding
- Promoter pledge
- Source
- Availability status

Indexes:

- Instrument ID and as-of date

### `corporate_events`

- Instrument ID
- Event date
- Known-as-of timestamp
- Event type
- Event description
- Event risk classification
- Source

Indexes:

- Instrument ID and event date
- Known-as-of timestamp

### `strategy_parameters`

- Parameter version
- Strategy version
- Parameter key
- Parameter value
- Value type
- Effective from
- Effective to
- Created timestamp
- Notes

Indexes:

- Strategy version and parameter version
- Parameter key

### `signals`

- Instrument ID
- Signal timestamp
- Strategy version
- Parameter version
- Setup type
- Market regime
- Raw score
- Normalized score
- Score class
- Entry price
- Stop price
- Target 1
- Target 2
- Risk/reward
- Hard filter status
- Rejection reasons
- Component score details
- Explanation data

Indexes:

- Signal timestamp
- Instrument ID and signal timestamp
- Strategy version and parameter version

### `backtest_runs`

- Backtest run ID
- Strategy version
- Parameter version
- Data source
- Universe definition
- Start date
- End date
- Initial capital
- Cost assumptions
- Slippage assumptions
- Execution model
- Status
- Created timestamp
- Completed timestamp

Indexes:

- Strategy version and parameter version
- Start date and end date

### `trades`

- Backtest run ID
- Instrument ID
- Setup type
- Signal timestamp
- Entry timestamp
- Entry price
- Stop price
- Target 1
- Target 2
- Exit timestamp
- Exit price
- Exit reason
- Quantity
- Costs
- Slippage
- Gross P&L
- Net P&L
- MFE
- MAE
- Holding sessions

Indexes:

- Backtest run ID
- Instrument ID
- Entry timestamp
- Exit timestamp

### `backtest_metrics`

- Backtest run ID
- Metric scope
- Scope key
- Total trades
- Win rate
- Loss rate
- Average win
- Average loss
- Expectancy
- Profit factor
- Maximum drawdown
- Sharpe
- Sortino
- Average holding period
- Target 1 hit rate
- Target 2 hit rate
- Stop-first rate
- Time-exit rate
- MFE
- MAE
- Consecutive losses

Indexes:

- Backtest run ID
- Metric scope and scope key

### `data_health`

- Data-health ID
- Job ID
- Data source
- Instrument ID
- Timeframe
- Start timestamp
- End timestamp
- Expected rows
- Received rows
- Missing intervals
- Duplicate rows
- Invalid rows
- Adjustment status
- Validation status
- Notes

Indexes:

- Instrument ID and timeframe
- Validation status
- Job ID

## Backtesting Architecture

The backtesting engine should be separated into clear modules:

- Universe selector
- Point-in-time data loader
- Indicator snapshot loader
- Strategy evaluator
- Signal filter
- Portfolio simulator
- Execution simulator
- Cost and slippage model
- Metrics calculator
- Persistence writer

Core requirements:

- Prevent look-ahead bias.
- Use 1-minute data where possible to resolve intrabar stop/target ordering.
- Conservatively assume stop first if ordering remains ambiguous.
- Persist run configuration and outputs.
- Preserve enough evidence to explain every generated or rejected signal.

Default capital:

- INR 10,00,000
- Configurable per backtest run

Risk per trade:

- 0.5% of current portfolio equity by default
- Configurable

Execution model:

- Breakout triggers are detected from completed 15-minute candles.
- Breakout entry uses the next available executable market price.
- If that executable price is beyond the configured maximum chase threshold above the trigger, mark the signal `GAP_EXTENDED` / `CHASE_AVOIDED`.
- Pullback confirmation uses a completed 15-minute candle.
- Pullback entry uses the next available executable market price.
- Future candle information must not be used.

Stop and target handling:

- Use 1-minute data where available to determine whether stop or target was reached first.
- If both are hit within the same 1-minute candle and ordering cannot be determined, assume stop first.
- If price gaps through the stop, execute at the first executable price rather than the theoretical stop.
- If price gaps through the target, execute at the first executable price rather than assuming an earlier target fill.

Trading costs:

- Use a configurable `TradingCostModel`.
- Support brokerage, STT, exchange transaction charges, SEBI charges, GST, stamp duty, and other applicable charges.
- Store cost rates with effective dates so historical backtests can reproduce assumptions.
- Initial values should be based on current Upstox published equity-delivery charges where applicable, but every parameter remains configurable.
- Do not assume current rates applied historically.

Slippage:

- Use a configurable slippage model.
- Initial research assumption: entry slippage 0.05%, exit slippage 0.05%.
- Future models may be fixed-percentage, spread-based, or liquidity-based.

Survivorship bias:

- Initial development may use currently available instruments while infrastructure is built.
- Research-grade backtesting must support a point-in-time universe.
- Do not claim V1 results are survivorship-bias-free until point-in-time universe support is implemented.

## Implementation Order

Major functionality must be built in this order:

1. Repository and project foundation
2. Documentation
3. Database
4. Upstox instrument synchronization
5. Historical data ingestion
6. Data validation
7. Indicator engine
8. Strategy engine
9. Backtesting engine
10. Performance analytics
11. Dashboard for backtest and research
12. Real-time Upstox WebSocket
13. Real-time scanner
14. Alerts

Do not build the live scanner before the backtester.

Do not implement automatic trading or order placement in V1.

## Implementation Milestones

### Milestone 0: Planning and Documentation

- Create core documentation.
- Confirm architecture.
- Confirm unresolved data and strategy questions.

### Milestone 1: Repository Foundation

- Initialize backend and frontend projects.
- Add Docker Compose for PostgreSQL, Redis, backend, Celery worker, and frontend.
- Add environment examples.
- Add Alembic configuration.
- Add health endpoints.
- Add logging.
- Add formatting, linting, and testing skeletons.

### Milestone 2: Database Foundation

- Define SQLAlchemy models.
- Add Alembic migrations.
- Add database session and configuration.
- Add initial health checks.

### Milestone 3: Market Data Foundation

- Implement provider interface.
- Implement Upstox OAuth configuration.
- Synchronize NSE equity instruments.
- Persist normalized instruments.

### Milestone 4: Historical Data Pipeline

- Ingest daily candles.
- Ingest 1-minute intraday candles where available.
- Derive 5-minute and 15-minute candles.
- Add data-health validation.

### Milestone 5: Indicator Engine

- Calculate required indicators internally.
- Persist daily technical values.
- Calculate relative strength and breadth.
- Add validation tests for indicator calculations.

### Milestone 6: Strategy Engine

- Load versioned parameters.
- Evaluate Strategy V1.1 deterministically.
- Persist signals, scores, explanations, and rejection reasons.

### Milestone 7: Backtesting Engine

- Implement point-in-time backtester.
- Add execution, slippage, costs, position constraints, and intrabar handling.
- Persist trades and metrics.

### Milestone 8: Research Dashboard

- Build dashboard views for instruments, charts, signals, backtest runs, metrics, and trade details.

### Milestone 9: Real-Time Scanner

- Add Upstox WebSocket integration.
- Maintain real-time read-only scanner state.
- Display live candidates.

### Milestone 10: Alerts

- Add configurable read-only alerts.

## Assumptions

- AlphaHunter remains single-user for V1.
- V1 is read-only and must not place orders.
- PostgreSQL and Redis are available through Docker Compose for local development.
- The authoritative strategy document is `docs/STRATEGY_V1_1.md`.
- Upstox is the initial provider, but the provider abstraction must remain broker-neutral.
- The repository is a monorepo with `backend/`, `frontend/`, `docs/`, `infra/`, and `tests/`.
- Celery plus Redis is the V1 background job system.
- Frontend tests stay simple and maintainable for the selected Next.js/TypeScript setup.
- Backtest starting capital defaults to INR 10,00,000 and is configurable.
- Default risk per trade is 0.5% of current portfolio equity and is configurable.
- Initial slippage assumption is 0.05% entry and 0.05% exit, both configurable.

## Unresolved Questions

- Which exact fields are available through the user's Upstox account and token scope during implementation?
- Which secondary source should be approved for delivery participation, promoter pledge, governance/regulatory risk, and structured earnings-calendar data if Upstox does not provide reliable point-in-time fields?
- What effective-dated historical brokerage/tax schedules should be used before the user has validated cost assumptions?
- What value should be used for the configurable maximum chase threshold beyond the existing `MAX_GAP` rule?
- What exact rules define clean consolidation, controlled pullback, valid support, selling pressure contraction, bullish 15-minute reversal, and confirmation volume if the strategy document remains ambiguous?
