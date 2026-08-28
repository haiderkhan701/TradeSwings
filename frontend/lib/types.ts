export type UpstoxStatus = {
  provider: string;
  configured: boolean;
  authenticated: boolean;
  token_available: boolean;
  token_source: string | null;
  token_expiry: string | null;
};

export type InstrumentSummary = {
  total_nse_equities: number;
  last_sync_timestamp: string | null;
  last_sync_status: string | null;
};

export type Instrument = {
  id: number;
  instrument_key: string;
  exchange: string;
  segment: string;
  instrument_type: string;
  isin: string | null;
  trading_symbol: string;
  name: string;
  short_name: string | null;
  lot_size: number;
  tick_size: string;
  active: boolean;
};

export type InstrumentList = {
  items: Instrument[];
  page: number;
  page_size: number;
  total: number;
};
