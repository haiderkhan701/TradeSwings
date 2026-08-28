import { getApiBaseUrl } from "@/lib/config";
import type { InstrumentList, InstrumentSummary, UpstoxStatus } from "@/lib/types";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getUpstoxStatus(): Promise<UpstoxStatus> {
  return getJson<UpstoxStatus>("/api/v1/upstox/status");
}

export function getInstrumentSummary(): Promise<InstrumentSummary> {
  return getJson<InstrumentSummary>("/api/v1/instruments/summary");
}

export function getInstruments(page: number, pageSize: number): Promise<InstrumentList> {
  return getJson<InstrumentList>(`/api/v1/instruments?page=${page}&page_size=${pageSize}`);
}
