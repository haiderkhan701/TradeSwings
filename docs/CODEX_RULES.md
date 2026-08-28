# AlphaHunter Codex Rules

This document defines project-specific rules for Codex and any future automated development assistance.

## Project Mission

AlphaHunter is a single-user, read-only NSE swing-trading research and scanning platform.

V1 must focus on:

- Market-data ingestion
- Indicator calculation
- Deterministic strategy evaluation
- Historical backtesting
- Research dashboard
- Later real-time read-only scanning

## Critical Rules

- Do not implement automatic order placement in V1.
- Do not implement live trading execution in V1.
- Do not implement broker order management in V1.
- Do not build the live scanner before the backtester.
- Do not invent or modify trading-strategy rules.
- Treat `docs/STRATEGY_V1_1.md` as the authoritative strategy specification.
- If an implementation ambiguity is discovered, document it, stop before inventing a rule, and ask for clarification.
- Create or review architecture and documentation before implementing major functionality.
- Keep strategy parameters configurable and versioned.
- Never put API secrets in source code.
- Never commit secrets or tokens to Git.
- Use environment variables and local `.env` files.
- Provide `.env.example` with placeholders only.
- Do not log secrets, access tokens, or refresh tokens.
- Design the market-data layer so Upstox can later be replaced without rewriting the strategy engine.
- Keep research/backtest data clearly separate from live market data.
- Do not introduce Kubernetes or other complex orchestration in V1.

## Required Development Order

Build major functionality in this order:

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

Celery plus Redis is the V1 background job system.

## Strategy Rules

Strategy modules must:

- Be deterministic
- Be explainable
- Use versioned parameters
- Include strategy version in outputs
- Include parameter version in outputs
- Preserve component-level scoring evidence
- Preserve hard-filter and rejection reasons

Strategy modules must not:

- Call Upstox APIs directly
- Use an LLM for trade decisions
- Use future data
- Hide failed filters
- Fabricate unavailable fields

## Market Data Rules

All market-data integrations must go through provider abstractions.

Initial provider:

```text
MarketDataProvider
  UpstoxProvider
```

Strategy and backtest code must depend on internal normalized data, not provider-specific response shapes.

## Data Integrity Rules

The system must:

- Prevent look-ahead bias
- Track data source
- Track data period
- Track ingestion status
- Track missing candles
- Track duplicate candles
- Track invalid candles
- Track adjustment status
- Timestamp market data correctly using Asia/Kolkata timezone
- Validate missing dates, duplicate candles, invalid OHLC relationships, zero or negative prices, abnormal volume, timestamp issues, timezone issues, duplicate instruments, and incomplete datasets before strategy/backtesting use.

The system must not silently fabricate missing data.

Optional unavailable fields must be explicitly marked unavailable or secondary-source required.

## Backtesting Rules

Backtesting must be implemented before real-time scanner deployment.

Backtesting must:

- Use point-in-time data
- Model gaps
- Model slippage
- Model Indian trading costs
- Handle stop/target ambiguity
- Use 1-minute data where possible to resolve intrabar ordering
- Conservatively assume stop first if ordering remains ambiguous
- Persist run configuration
- Persist strategy version
- Persist parameter version
- Persist trades and metrics
- Use configurable starting capital. The default is INR 10,00,000.
- Use 0.5% of current portfolio equity as the default risk per trade.
- Use configurable position limits.
- Use configurable trading-cost and slippage models.
- Store trading-cost assumptions with effective dates.
- Do not claim survivorship-bias-free results until point-in-time universe support exists.

## Security Rules

Do not commit:

- `.env`
- API keys
- Client secrets
- Access tokens
- Refresh tokens
- Broker session files
- Downloaded private account data

Do provide:

- `.env.example`
- Configuration documentation
- Clear local setup instructions

## Documentation Rules

When strategy behavior changes, update:

- `docs/STRATEGY_V1_1.md`, or create a new versioned strategy document
- Parameter documentation
- Tests that enforce the behavior

When data behavior changes, update:

- `docs/DATA_SPEC_V1.md`
- Data migrations if needed
- Data-health checks

When backtest behavior changes, update:

- `docs/BACKTEST_SPEC_V1.md`
- Backtest fixtures and tests

When architecture changes materially, update:

- `docs/ARCHITECTURE.md`
