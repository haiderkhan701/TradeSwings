# AlphaHunter Backtest Specification V1

This document defines the requirements for AlphaHunter backtesting.

Backtesting is mandatory before real-time scanner deployment.

## Scope

The V1 backtester evaluates deterministic Strategy V1.1 signals on historical NSE equity data.

It must support:

- Long-only trades
- Breakout setup
- Pullback setup
- Maximum 15-session holding period
- Maximum 5 simultaneous positions
- Maximum 80% capital deployment
- Maximum 2 positions per sector
- Target 1 at +5%
- Target 2 at +6%
- Minimum risk/reward of 1:2

## Non-Goals

The V1 backtester must not:

- Place live orders
- Simulate broker order-management APIs
- Trade options
- Trade futures
- Use an LLM to make trade decisions

## Required Inputs

Each backtest run must define:

- Strategy version
- Parameter version
- Market universe
- Data source
- Data period
- Initial capital
- Slippage assumptions
- Indian trading-cost assumptions
- Execution model
- Risk settings
- Position constraints

Default starting capital:

```text
INR 10,00,000
```

Starting capital must be configurable per backtest run.

## Point-in-Time Behavior

The backtester must prevent look-ahead bias.

Rules:

- Signal evaluation must use only data available at the signal timestamp.
- Daily indicators must use completed historical daily candles only.
- Intraday confirmations must use completed intraday candles only.
- Corporate actions, fundamentals, ownership, and events must be handled using known-as-of dates where available.

## Execution Model

The execution model must be realistic and configurable.

It must model:

- Entry execution
- Gaps
- Slippage
- Indian trading costs
- Stops
- Targets
- Time exits
- Intrabar ambiguity

Where possible, use 1-minute data to resolve intrabar ordering.

If stop/target ordering remains ambiguous, conservatively assume stop first.

### Breakout Entry

- Detect the trigger using the completed 15-minute candle.
- Entry occurs at the next available executable market price.
- Do not assume execution at the exact breakout threshold.
- If the next executable price is more than the configured maximum chase threshold above the trigger, mark the signal as `GAP_EXTENDED` / `CHASE_AVOIDED` instead of entering.

### Pullback Entry

- Detect the completed 15-minute confirmation candle.
- Entry occurs at the next available executable price.
- Do not use future candle information.

### Stop and Target Execution

- Use 1-minute data where available to determine whether stop or target was reached first.
- If both are hit within the same 1-minute candle and ordering cannot be determined, assume stop first.
- If price gaps through the stop, simulate execution at the first executable price rather than the theoretical stop price.
- If price gaps through the target, simulate execution at the first executable price rather than assuming an earlier target fill.

## Gap Handling

Initial `MAX_GAP`: 2%.

If price gaps more than 2% above the intended trigger:

- Do not chase
- Mark as `GAP_EXTENDED`
- Do not create a normal fresh entry

## Stops and Targets

Targets:

- Target 1: +5%
- Target 2: +6%

Stops:

- Breakout: structural breakout stop plus volatility buffer
- Pullback: recent swing-low or support stop plus volatility buffer

Initial ATR buffer:

```text
0.2 * ATR14
```

## Position Sizing

Default risk per trade:

```text
0.5% of current portfolio equity
```

Quantity:

```text
floor(risk_amount / abs(entry - stop))
```

Apply:

- Available capital
- Maximum capital deployment
- Maximum simultaneous positions
- Maximum positions per sector
- Lot and tick constraints where applicable

## Portfolio Constraints

Initial constraints:

- Maximum simultaneous positions: 5
- Maximum capital deployment: 80%
- Maximum positions from one sector: 2
- Maximum initial holding period: 15 trading sessions

All position limits are configurable.

## Trading Cost Model

Do not hard-code brokerage or tax values throughout the code.

Create a configurable `TradingCostModel` that supports:

- Brokerage
- STT
- Exchange transaction charges
- SEBI charges
- GST
- Stamp duty
- Other applicable charges

Store rates with an effective date so historical backtests can reproduce the appropriate cost assumptions.

Initially use the current Upstox published equity-delivery cost schedule where applicable, but make every parameter configurable.

Do not assume today's rates were applicable historically.

## Slippage Model

Create a configurable slippage model.

Initial research assumption:

- Entry slippage: 0.05%
- Exit slippage: 0.05%

Do not treat this as a proven value.

Future models may include:

- Fixed percentage
- Spread-based
- Liquidity-based

## Trade Lifecycle

Each simulated trade should track:

- Backtest run ID
- Instrument
- Symbol
- Sector
- Setup type
- Signal timestamp
- Entry timestamp
- Entry price
- Stop price
- Target 1 price
- Target 2 price
- Exit timestamp
- Exit price
- Exit reason
- Quantity
- Risk amount
- Position value
- Costs
- Slippage
- Gross P&L
- Net P&L
- MFE
- MAE
- Strategy version
- Parameter version

## Exit Reasons

Expected exit reasons include:

- `TARGET_1`
- `TARGET_2`
- `STOP`
- `TIME_EXIT`
- `GAP_EXTENDED`
- `HARD_FILTER_FAILED`
- `DATA_UNAVAILABLE`
- `AMBIGUOUS_STOP_FIRST`

Additional exit or rejection reasons may be added if documented.

## Required Metrics

Calculate:

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
- +5% hit rate
- +6% hit rate
- Stop-first rate
- Time-exit rate
- MFE
- MAE
- Consecutive losses

## Required Breakdowns

Break down results by:

- Setup type
- Score bucket
- Market regime
- Sector
- Year
- Month

## Output Requirements

Every backtest run must persist:

- Run configuration
- Strategy version
- Parameter version
- Data source
- Data period
- Universe definition
- Costs and slippage assumptions
- Summary metrics
- Breakdown metrics
- Simulated trades
- Data-health warnings

Backtest results shown in the dashboard must be traceable to persisted run records.

## Data Quality and Health

Backtests must surface data issues instead of hiding them.

Track:

- Missing candles
- Duplicate candles
- Invalid OHLCV rows
- Insufficient lookback
- Missing intraday data
- Unavailable delivery data
- Unavailable fundamental data
- Corporate-action adjustment uncertainty

If data is insufficient for a signal or trade simulation, the result should be marked with an explicit reason.

## Survivorship Bias

V1 limitation:

- The initial development universe may use currently available instruments while infrastructure is being built.

Research-grade backtester requirement:

- Support a point-in-time universe so delisted or deactivated securities are not automatically excluded from historical research.

Do not claim that V1 results are survivorship-bias-free until this is implemented.
