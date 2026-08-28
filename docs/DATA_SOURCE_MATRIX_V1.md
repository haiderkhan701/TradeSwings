# AlphaHunter Data Source Matrix V1

This matrix records the first-pass availability review against current Upstox developer documentation.

Sources reviewed:

- Upstox Instrument files: https://upstox.com/developer/api-documentation/instruments/
- Upstox Historical Candle Data V3: https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/
- Upstox Intraday Candle Data V3: https://upstox.com/developer/api-documentation/v3/get-intra-day-candle-data/
- Upstox Market Quote: https://upstox.com/developer/api-documentation/market-quote/
- Upstox Market Data Feed V3: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- Upstox Market Information: https://upstox.com/developer/api-documentation/market-information/
- Upstox Fundamentals: https://upstox.com/developer/api-documentation/fundamentals/
- Upstox Company Profile: https://upstox.com/developer/api-documentation/get-company-profile/
- Upstox Balance Sheet: https://upstox.com/developer/api-documentation/get-balance-sheet/
- Upstox Income Statement: https://upstox.com/developer/api-documentation/get-income-statement/
- Upstox Share Holdings: https://upstox.com/developer/api-documentation/get-share-holdings/
- Upstox Corporate Actions: https://upstox.com/developer/api-documentation/get-corporate-actions/
- Upstox News: https://upstox.com/developer/api-documentation/news/
- Upstox Brokerage Details: https://upstox.com/developer/api-documentation/get-brokerage/
- Upstox Brokerage Charges: https://upstox.com/brokerage-charges/

Do not implement an external paid data provider in V1 until Upstox field availability and quality have been verified in code.

## Milestone 2 Sources

| Data field/category | Provider | Endpoint/source | Authentication requirement | Response type | Update frequency | Historical availability | Known limitations | Implementation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OAuth authorization login | Upstox | `GET https://api.upstox.com/v2/login/authorization/dialog` | Client ID/API key and registered redirect URI; user signs in on Upstox | HTTP redirect with single-use `code` and returned `state` | User initiated; access token expires at 3:30 AM the following day per Upstox docs | Not historical | Redirect URI must exactly match the developer app; state must be validated; no app should handle Upstox user credentials directly | Implemented in Milestone 2 |
| OAuth token exchange | Upstox | `POST https://api.upstox.com/v2/login/authorization/token` | Backend-only Client ID, Client Secret, redirect URI, single-use authorization code | JSON token response containing access token and safe metadata | User initiated after authorization; token expiry is normal | Not historical | Client secret must never be exposed to frontend; authorization code is single-use; tokens must not be logged or returned by APIs | Implemented in Milestone 2 |
| NSE equity instrument universe | Upstox | `https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz` | No bearer token required for public BOD file | Gzipped JSON list of instrument records | Daily refresh around 6 AM, with rare intraday refreshes as needed | Current BOD file only; next-day BOD file excludes delisted stocks and expired contracts | Not a point-in-time historical universe; must use `instrument_key`, not `exchange_token`, as provider unique ID; AlphaHunter filters `exchange=NSE`, `segment=NSE_EQ`, `instrument_type=EQ` | Implemented in Milestone 2 |
| Suspended instruments | Upstox | `https://assets.upstox.com/market-quote/instruments/exchange/suspended.json.gz` | No bearer token required for public file | Gzipped JSON list of suspended instruments | Daily BOD source | Current suspended list; historical suspension state needs separate point-in-time support | Used only to exclude current suspended instruments; does not solve survivorship bias | Implemented in Milestone 2 |
| Historical candles | Upstox | `GET https://api.upstox.com/v3/historical-candle/:instrument_key/:unit/:interval/:to_date/:from_date` | Bearer access token | JSON object with `data.candles` arrays: timestamp, OHLC, volume, OI | On request | Minutes/hours from January 2022; days/weeks/months from January 2000 with retrieval-window limits | Documented only in Milestone 2; historical ingestion is not implemented yet; must preserve Asia/Kolkata timestamps and avoid look-ahead bias later | Documented only; not implemented |

| Field | Required? | Upstox API available? | Upstox endpoint | Update frequency | Historical availability | Fallback source required? | Fallback source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NSE equity instruments | Yes | Yes | Instrument files / Instrument Search | Daily BOD plus search | Current BOD; point-in-time universe still needs historical support | Later for survivorship-bias-free research | NSE bhavcopy/archive or another approved source, not implemented yet |
| Suspended instruments | Yes | Yes | Suspended instruments file | Daily BOD | Current list; historical status needs validation | Later for historical point-in-time status | NSE archive or another approved source, not implemented yet |
| Instrument ISIN | Yes | Yes | Instrument files | Daily BOD | Current BOD; historical mapping needs validation | Possibly | NSE archive if historical symbol/ISIN changes are needed |
| Sector classification | Yes for sector scoring | Partial | Company Profile API | Provider-defined refresh cadence | Current/profile history not guaranteed by doc | Yes for point-in-time sector history | Secondary-source required; not implemented yet |
| Market capitalization | Required where reliable | Partial | Company Profile API sector market-cap fields; company-level market-cap availability must be verified | Provider-defined refresh cadence | Historical availability not guaranteed by doc | Yes if company-level field is unavailable or not point-in-time | Secondary-source required; not implemented yet |
| Daily OHLCV | Yes | Yes | Historical Candle Data V3 | On request | Days available from January 2000 per docs | No for price history if access works | None initially |
| 1-minute historical OHLCV | Yes where available | Yes | Historical Candle Data V3 | On request | Minutes available from January 2022 per docs with retrieval-window limits | No for available period; yes for older intraday | None initially |
| Current-day intraday OHLCV | Yes for live/research later | Yes | Intraday Candle Data V3 | On request during trading day | Current trading day endpoint | No | None initially |
| 5-minute and 15-minute candles | Yes | Derive internally | Derived from stored 1-minute candles; Upstox can also return intervals | Internal calculation cadence | Same as source 1-minute availability | No | None initially |
| Real-time LTP/quote | Later | Yes | Market Quote V3 / Market Data Feed V3 | Real time | Not historical | No | None initially |
| Bid/ask spread | Optional for liquidity | Yes for live feed/quotes where full depth is available | Market Data Feed V3 full mode / Market Quote | Real time | Historical bid/ask not guaranteed | Yes for historical spread modeling | Secondary-source required; not implemented yet |
| Open interest | Optional/relevant where available | Yes, mostly derivatives-oriented | Market Information OI / market feed fields | Intraday/live | Historical equity OI not applicable; derivatives excluded from V1 | Not for V1 equities | None initially |
| Delivery participation | Optional confirmation | Not verified in reviewed docs | None verified | Unknown | Unknown | Yes | Secondary-source required; not implemented yet |
| Revenue trend | Optional safety score | Yes | Income Statement API | Financial reporting cadence | Historical values reported by endpoint | No if endpoint access and as-of dating are sufficient | None initially |
| Earnings trend | Optional safety score | Yes | Income Statement API | Financial reporting cadence | Historical values reported by endpoint | No if endpoint access and as-of dating are sufficient | None initially |
| Profitability | Optional safety score | Yes | Income Statement / Key Ratios API | Financial reporting cadence | Historical availability to verify per response | Possibly | Secondary-source required if fields are incomplete |
| Debt | Optional safety score | Yes | Balance Sheet API | Financial reporting cadence | Historical balance-sheet periods | No if endpoint access and as-of dating are sufficient | None initially |
| Promoter pledge | Optional safety/red flag | Not verified in reviewed docs | Share Holdings may include ownership categories, but pledge field must be verified | Quarterly if available | Historical availability unknown | Yes | Secondary-source required; not implemented yet |
| Shareholding / ownership | Optional safety score | Yes | Share Holdings API | Quarterly | Multiple reporting quarters shown in docs | No if endpoint access and known-as-of dating are sufficient | None initially |
| Governance/audit/regulatory concerns | Optional safety/red flag | Partial | News API and corporate actions may help but do not equal a structured risk feed | Provider/news cadence | Historical article availability must be verified | Yes | Secondary-source required; not implemented yet |
| Corporate actions: dividends, bonus, splits, rights | Yes for data adjustment/audit | Yes | Corporate Actions API | Event-driven | Event list with announcement/ex/record details | No if endpoint access and history are sufficient | None initially |
| Earnings calendar / board meetings | Required for event risk if available | Partial | News API may surface articles; no structured calendar endpoint verified | Provider/news cadence | Historical availability must be verified | Yes | Secondary-source required; not implemented yet |
| Major orders, acquisitions, capacity expansion, management changes | Optional event risk | Partial | News API | Provider/news cadence | Historical availability must be verified | Yes | Secondary-source required; not implemented yet |
| Market holidays | Yes | Yes | Market Holidays API | Current year per docs | Current-year list; historical holiday support must be verified | Possibly | NSE holiday archives if needed |
| Market timings/status | Yes | Yes | Market Timings / Exchange Status APIs | Daily/live | Date-specific timings; historical depth must be verified | Possibly | NSE calendar if needed |
| Brokerage/charges preview | Required for configurable cost model calibration | Yes | Brokerage Details API | On request/current rates | Not a historical rate archive | Yes for historical cost reproducibility | Store effective-dated configured rates in AlphaHunter |

## Implementation Notes

- Optional fields unavailable through Upstox must be marked unavailable or `secondary_source_required`.
- Missing optional data must not be fabricated.
- Strategy V1.1 must remain deterministic when optional data is unavailable.
- Backtests must not use today's fundamentals, ownership, sector classification, or event data for historical decisions unless known-as-of dating is available.
