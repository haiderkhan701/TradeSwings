"use client";

import { useEffect, useState } from "react";

import { getInstruments, getInstrumentSummary, getUpstoxStatus } from "@/lib/api";
import type { Instrument, InstrumentSummary, UpstoxStatus } from "@/lib/types";

const PAGE_SIZE = 25;

type LoadState = {
  status: UpstoxStatus | null;
  summary: InstrumentSummary | null;
  instruments: Instrument[];
  total: number;
  error: string | null;
};

export function InstrumentVerification() {
  const [page, setPage] = useState(1);
  const [state, setState] = useState<LoadState>({
    status: null,
    summary: null,
    instruments: [],
    total: 0,
    error: null
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [status, summary, instruments] = await Promise.all([
          getUpstoxStatus(),
          getInstrumentSummary(),
          getInstruments(page, PAGE_SIZE)
        ]);

        if (!cancelled) {
          setState({
            status,
            summary,
            instruments: instruments.items,
            total: instruments.total,
            error: null
          });
        }
      } catch {
        if (!cancelled) {
          setState((current) => ({
            ...current,
            error: "Backend data is unavailable"
          }));
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(state.total / PAGE_SIZE));

  return (
    <section className="verification">
      <div className="metric-row">
        <Metric
          label="Upstox connection"
          value={state.status?.authenticated ? "CONNECTED" : "NOT CONNECTED"}
        />
        <Metric
          label="Instrument database"
          value={`${state.summary?.total_nse_equities ?? 0} NSE equities`}
        />
        <Metric
          label="Last synchronization"
          value={
            state.summary?.last_sync_timestamp
              ? new Date(state.summary.last_sync_timestamp).toLocaleString()
              : "Not synced"
          }
        />
      </div>

      {state.error ? <p className="error-text">{state.error}</p> : null}

      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Company</th>
              <th>ISIN</th>
              <th>Instrument Key</th>
              <th>Tick Size</th>
              <th>Lot Size</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {state.instruments.map((instrument) => (
              <tr key={instrument.instrument_key}>
                <td>{instrument.trading_symbol}</td>
                <td>{instrument.name}</td>
                <td>{instrument.isin ?? "-"}</td>
                <td>{instrument.instrument_key}</td>
                <td>{instrument.tick_size}</td>
                <td>{instrument.lot_size}</td>
                <td>{instrument.active ? "Yes" : "No"}</td>
              </tr>
            ))}
            {state.instruments.length === 0 ? (
              <tr>
                <td colSpan={7}>No instruments synchronized yet.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="pager" aria-label="Instrument pagination">
        <button type="button" onClick={() => setPage((value) => Math.max(1, value - 1))}>
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
        >
          Next
        </button>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
