# AlphaHunter Data Specification V1

This document defines the data requirements for AlphaHunter V1.

AlphaHunter is initially a single-user, read-only NSE swing-trading research and scanning platform. The first market-data provider is Upstox, but the data model must allow the provider to be changed later without rewriting the strategy engine.

## Data Principles

- Use provider abstraction for market data.
- Do not allow strategy modules to call Upstox APIs directly.
- Never store API secrets in source code.
- Never commit secrets or tokens to Git.
- Use environment variables and local `.env` files.
- Provide `.env.example` with placeholder values only.
- Do not silently fabricate missing data.
- Prevent look-ahead bias.
- Timestamp market data correctly using Asia/Kolkata timezone.
- Track data source and ingestion metadata.

## Primary Provider

Initial provider:

```text
MarketDataProvider
  UpstoxProvider
```

Conceptual provider methods:

- `get_instruments()`
- `get_historical_candles()`
- `get_quote()`
- `subscribe_market_feed()`
- `get_market_data()`

Use the current official Upstox API documentation when implementing the integration.

## Upstox Authentication

Use the appropriate Upstox OAuth flow.

Keep the following outside source code:

- Client ID
- Client secret
- Redirect URI
- Access tokens
- Refresh tokens, if applicable

Secrets and tokens must not be logged.

## Initial Upstox Data Requirements

Initially retrieve:

- NSE equity instruments
- Historical OHLCV data
- Intraday historical candles where available

Later retrieve:

- Live market feed and WebSocket data
- OI where available and relevant

Do not assume that every fundamental or shareholding field visible in the Upstox consumer app is available through the developer API. Verify each API field before depending on it.

Field availability is tracked in `docs/DATA_SOURCE_MATRIX_V1.md`.

Initial documentation review found Upstox developer endpoints for instruments, historical candles, market quotes, live market feed, company profile, balance sheet, income statement, shareholdings, corporate actions, news, market holidays/timings/status, and brokerage details. Each field must still be validated against the user's actual API access and response payloads before implementation depends on it.

Do not introduce a third-party paid data provider until Upstox availability has been verified in code. Fields not available through Upstox must be marked `secondary_source_required`.

## Market Universe

Initial universe:

- NSE listed equities

Excluded:

- SME stocks
- Suspended or restricted securities
- Extremely illiquid stocks
- Penny stocks
- Securities that fail liquidity rules
- Futures
- Options
- ETFs
- Commodities
- Crypto

Reference data:

- Nifty 50
- Sector indices
- Other indices only when needed for market-regime or sector-strength calculations

## Configurable Universe Filters

Initial configurable filters:

- Minimum price: INR 100
- Minimum market capitalization: INR 2,000 crore where reliable data is available
- Minimum 20-day average traded value: INR 10 crore

These filters are configurable research parameters.

## Historical Data

Target history:

- Up to 5 years where available

Required:

- Daily OHLCV
- Intraday 1-minute candles where available and appropriate

Derived:

- 5-minute candles
- 15-minute candles

Storage preference:

- Store raw 1-minute data where possible.
- Derive higher intraday timeframes internally.
- Prefer adjusted data for technical-indicator calculations where appropriate.
- Preserve raw/original market data when available.
- Do not mix adjusted and unadjusted prices within the same calculation.

Daily indicators require at least 250 trading sessions.

## Timezone

All exchange timestamps must be interpreted and stored consistently with Asia/Kolkata exchange time.

Recommended storage approach:

- Store timestamps as timezone-aware values where supported.
- Normalize provider timestamps during ingestion.
- Retain provider raw timestamp fields only if helpful for auditing.

## Data Quality Requirements

Handle:

- Market holidays
- Missing candles
- Duplicate candles
- Bad or invalid OHLCV values
- Corporate actions
- Splits and bonuses where reliable adjusted data is available

The system must not silently fabricate missing candles or adjusted values.

## Corporate Actions

Corporate actions should be tracked when reliable data is available:

- Splits
- Bonuses
- Dividends
- Symbol changes
- Mergers or demergers
- Suspensions
- Other exchange or corporate events relevant to price history

Historical analysis must record whether data is adjusted, unadjusted, or partially adjusted.

Raw price series and adjusted price series must be documented clearly once the provider payloads are verified.

## Fundamentals and Ownership

Fundamentals and ownership are useful for strategy safety checks, but availability must be verified per source.

Track reliable fields for:

- Revenue trend
- Earnings trend
- Profitability
- Debt
- Promoter pledge
- Governance, audit, and regulatory concerns
- Shareholding or ownership data, when available

If reliable delivery, fundamentals, or ownership data is unavailable, record the field as unavailable rather than inventing a value.

## Initial Logical Tables

- `instruments`
- `daily_candles`
- `intraday_candles`
- `technical_daily`
- `market_indices`
- `sector_indices`
- `relative_strength`
- `fundamentals`
- `ownership`
- `corporate_events`
- `signals`
- `trades`
- `strategy_parameters`
- `backtest_runs`
- `backtest_metrics`
- `data_health`

## Indexing Requirements

Use appropriate indexes for:

- Instrument identifiers
- Symbol
- Date
- Timestamp
- Timeframe
- Strategy version
- Parameter version
- Backtest run ID

Historical candle storage must support efficient queries by:

- Instrument and date range
- Instrument and intraday timestamp range
- Universe scan date
- Backtest period

## Data Health

The `data_health` area should track:

- Ingestion job
- Data source
- Instrument
- Timeframe
- Expected rows
- Received rows
- Missing intervals
- Duplicate rows
- Invalid rows
- Adjustment status
- Validation status
- Notes or error details

Before strategy or backtesting uses historical data, validate:

- Missing dates
- Duplicate candles
- Invalid OHLC relationships
- Zero or negative prices
- Abnormal volume
- Timestamp issues
- Timezone issues
- Duplicate instruments
- Incomplete datasets

The backtester must be able to reject or flag incomplete data instead of silently continuing.

## Look-Ahead Bias Controls

The system must prevent using information that was not available at the decision timestamp.

Examples:

- A signal generated on date D must not use candle data after D.
- A 15-minute confirmation must use only completed 15-minute candles.
- Fundamental, ownership, and corporate-event data must include effective or known-as-of dates where available.
- Backtests must record data source, period, strategy version, and parameter version.

Point-in-time rules apply to:

- Prices
- Indicators
- Fundamentals
- Ownership
- Corporate events
- Earnings dates
- Sector classification where applicable

Do not use today's fundamentals, shareholding, sector classification, or corporate-event values to backtest historical trades unless known-as-of dating proves they were available at the simulated timestamp.

## Research and Live Data Separation

Clearly separate:

- Research/backtest data
- Live market data

The same strategy engine should be able to consume normalized data from either source so backtest and live behavior use the same calculations.

## Survivorship Bias

V1 limitation:

- The initial development universe may use currently available instruments while infrastructure is being built.

Research-grade backtesting requirement:

- Support a point-in-time universe so delisted or deactivated securities are not automatically excluded from historical research.

Do not claim that V1 results are survivorship-bias-free until point-in-time universe support is implemented.
