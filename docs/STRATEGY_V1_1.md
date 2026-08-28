# AlphaHunter Strategy V1.1

This document is the authoritative specification for AlphaHunter Strategy V1.1.
Implementation must not invent, modify, or reinterpret strategy rules outside this document without an explicit strategy-spec update.

## Scope

Strategy V1.1 is a deterministic, explainable, rules-based swing-trading strategy for NSE listed equities.

The strategy is read-only in V1. It may generate research candidates, signals, scores, entries, stops, targets, position sizes, and backtest trades, but it must not place orders or manage live broker orders.

## Non-Goals

- Automatic order placement
- Live trading execution
- Broker order management
- Options trading
- Futures trading
- LLM-based trade decisions

An LLM must never decide whether a stock is a trade.

## Trading Intent

- Direction: long-only
- Market: NSE equities
- Target: approximately 5% to 6%
- Maximum initial holding period: 15 trading sessions
- Minimum risk/reward: 1:2
- Default risk per trade: 0.5% of current portfolio equity
- Maximum simultaneous positions: 5
- Maximum capital deployment: 80%
- Maximum positions from one sector: 2

## Strategy Versioning

Every strategy result must include:

- `strategy_version`
- `parameter_version`

Initial strategy version:

```text
V1.1
```

Every backtest must record:

- Strategy version
- Parameter version
- Data period
- Data source

Strategy parameters must be configurable and versioned. They must not be scattered as untracked hard-coded constants throughout the codebase.

Example parameters:

- `MIN_PRICE`
- `MIN_AVG_TURNOVER`
- `MIN_SCORE`
- `BREAKOUT_BUFFER`
- `MIN_RVOL`
- `TARGET_1`
- `TARGET_2`
- `MIN_RR`
- `MAX_GAP`
- `RISK_PER_TRADE`
- `MAX_POSITIONS`
- `MAX_SECTOR_POSITIONS`
- `MAX_HOLDING_DAYS`

## Market Universe

Initial universe:

- NSE listed equities

Excluded from V1:

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

Indices and sector indices may be used as reference data for market-regime and sector-strength calculations.

## Configurable Universe Filters

Initial configurable research filters:

- Minimum price: INR 100
- Minimum market capitalization: INR 2,000 crore, where reliable data is available
- Minimum 20-day average traded value: INR 10 crore

These are configurable research parameters, not permanent assumptions.

## Required Indicators and Derived Inputs

Indicators must be calculated internally rather than sourced from external indicator APIs.

Required daily indicators:

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
- 252-day high, where data permits
- Support and resistance levels

Relative strength:

- RS5
- RS20
- RS60
- Sector RS20

Market breadth:

- Advances
- Declines
- Percentage of eligible stocks above 20 EMA
- Percentage of eligible stocks above 50 DMA
- Percentage of eligible stocks above 200 DMA

Daily indicators require at least 250 trading sessions where applicable.

## Market Regime

Nifty 50 is the primary benchmark.

Market regime score maximum: 15.

Rules:

| Condition | Points |
| --- | ---: |
| Nifty > 20 EMA | 3 |
| Nifty > 50 EMA | 3 |
| Nifty > 200 DMA | 3 |
| 20 EMA > 50 EMA | 2 |
| 50 DMA > 200 DMA | 2 |
| More than 50% of eligible stocks above 50 DMA | 2 |

Classification:

| Score | Classification |
| --- | --- |
| 12-15 | Bullish |
| 8-11 | Neutral |
| 0-7 | Bearish |

Normal long signals are not generated during a Bearish market regime.

## Sector Score

Sector score maximum: 10.

| Condition | Points |
| --- | ---: |
| Sector 5D RS > 0 | 3 |
| Sector 20D RS > 0 | 3 |
| Sector > 20 EMA | 2 |
| Sector > 50 DMA | 2 |

## Stock Trend Score

Stock trend score maximum: 15.

| Condition | Points |
| --- | ---: |
| Price > EMA20 | 3 |
| Price > EMA50 | 3 |
| Price > SMA200 | 3 |
| EMA20 > EMA50 | 3 |
| SMA50 > SMA200 | 3 |

## Relative Strength Score

Relative strength score maximum: 15.

| Condition | Points |
| --- | ---: |
| RS5 > 0 | 3 |
| RS20 > 0 | 4 |
| RS60 > 0 | 3 |
| Stock outperforming sector over 20D | 5 |

## Technical Setups

Strategy V1.1 supports two initial setups:

- Breakout
- Pullback

### Breakout Setup

Breakout setup components:

- 20-day resistance
- Price breaks resistance
- Breakout buffer initially 0.3%
- Volume confirmation
- Clean consolidation
- Sufficient target room

### Pullback Setup

Pullback setup components:

- Established uptrend
- Controlled correction
- Support
- No structural breakdown
- Bullish 15-minute reversal
- Confirmation volume

## Volume

Daily RVOL:

```text
current volume / previous 20-session average volume
```

Volume score maximum: 10.

| RVOL | Points |
| --- | ---: |
| < 1.0 | 0 |
| 1.0-1.25 | 2 |
| 1.25-1.5 | 4 |
| 1.5-2.0 | 7 |
| > 2.0 | 10 |

Breakout trigger requires RVOL >= 1.5.

## Momentum

Momentum score maximum: 5.

RSI14 rules:

| Condition | Points |
| --- | ---: |
| RSI > 50 | 2 |
| RSI rising | 2 |
| RSI 55-70 | 1 |

Do not award extra points for RSI > 70.

## Liquidity

Liquidity score maximum: 10.

Consider:

- Average traded value
- Bid/ask spread, where reliable data exists
- Trading frequency
- Volume consistency
- Price impact, where reliable data exists

Liquidity score below 5 is a hard rejection.

## Delivery

Delivery participation is a secondary confirmation when reliable data is available.

Delivery score maximum: 5.

Delivery data alone must not generate a signal.

If reliable delivery data is unavailable, mark the field as unavailable rather than fabricating a value.

## Fundamental Safety

Fundamental safety score maximum: 5.

Use available reliable data for:

- Earnings trend
- Revenue trend
- Profitability
- Debt
- Promoter pledge
- Governance, audit, and regulatory concerns

Severe fundamental or corporate red flags can hard-reject a stock.

## Catalyst and Event Risk

Track:

- Earnings
- Board meetings
- Major orders
- Acquisitions
- Capacity expansion
- Regulatory events
- Management changes
- Other major corporate announcements

Earnings event-risk rules:

| Timing | Classification |
| --- | --- |
| Within 1 trading session | High event risk |
| Within 2 trading sessions | Medium event risk |

V1 must not generate a fresh normal long entry when high earnings event risk exists.

## Gap Risk

Initial `MAX_GAP`: 2%.

If price gaps more than 2% above the intended trigger:

- Do not chase
- Mark the candidate as `GAP_EXTENDED`

## Extended Stock

If price is more than 10% above EMA20:

- Mark the candidate as `EXTENDED`
- Do not automatically reject it from research
- Do not generate a fresh chase entry without a new setup

## Total Score

Raw component maximums:

| Component | Maximum Points |
| --- | ---: |
| Market | 15 |
| Sector | 10 |
| Trend | 15 |
| Relative strength | 15 |
| Technical setup | 15 |
| Volume | 10 |
| Momentum | 5 |
| Liquidity | 10 |
| Delivery | 5 |
| Fundamentals | 5 |
| Catalyst | 5 |
| Total | 110 |

Normalized score:

```text
raw score / 110 * 100
```

Classification:

| Normalized Score | Class |
| --- | --- |
| 85-100 | A+ |
| 75-84 | A |
| 65-74 | B |
| 55-64 | C |
| < 55 | Reject |

Minimum score for trade trigger: 75.

## Hard Filters

Reject if any of the following is true:

- Bearish market regime
- Liquidity score < 5
- Minimum liquidity requirement failed
- Structural stop cannot be determined
- Risk/reward < 2
- Target room < 5%
- Severe fundamental or corporate risk
- High earnings event risk
- Excessive gap or chase condition

## Breakout Trigger

All conditions are required:

- Score >= 75
- Market is not Bearish
- Price breaks R20
- Price >= R20 * 1.003
- RVOL >= 1.5
- Completed 15-minute candle closes above breakout level
- Target room >= 5%
- Risk/reward >= 2
- Liquidity score >= 5
- No high event risk
- No severe fundamental red flag
- No excessive gap

## Pullback Trigger

All conditions are required:

- Score >= 75
- Market is not Bearish
- EMA20 > EMA50
- Price > SMA50
- Controlled pullback
- Valid support
- Selling pressure contraction
- Bullish 15-minute reversal
- Confirmation volume
- Target room >= 5%
- Risk/reward >= 2
- Liquidity score >= 5
- No high event risk
- No severe fundamental red flag

## Targets

- Target 1: +5%
- Target 2: +6%

## Stops

Breakout stop:

- Structural breakout stop plus volatility buffer

Pullback stop:

- Recent swing-low or support stop plus volatility buffer

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
- Maximum deployment
- Lot and tick constraints where applicable

All position limits and risk settings are configurable through versioned strategy parameters.

## Determinism and Explainability

Every signal must be reproducible from:

- Input market data
- Input reference data
- Strategy version
- Parameter version
- Timestamp

Every generated candidate or signal should retain enough component-level evidence to explain:

- Included conditions
- Failed conditions
- Hard rejection reasons
- Component scores
- Final normalized score
- Setup type
- Entry, stop, target, and risk/reward calculation

If an implementation ambiguity is discovered, document the ambiguity and ask for clarification before inventing a rule.
