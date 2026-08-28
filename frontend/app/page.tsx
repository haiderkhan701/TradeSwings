import { getApiBaseUrl } from "@/lib/config";
import { InstrumentVerification } from "./instrument-verification";

export default function Home() {
  return (
    <main className="shell">
      <section className="panel">
        <p className="eyeline">Milestone 2 Verification</p>
        <h1>AlphaHunter</h1>
        <p>
          Upstox authentication and NSE equity instrument synchronization are the only active
          implementation areas in this milestone.
        </p>
        <ul className="status-list" aria-label="Foundation status">
          <li>
            <strong>Backend API</strong>
            <span>{getApiBaseUrl()}</span>
          </li>
          <li>
            <strong>Mode</strong>
            <span>Read-only</span>
          </li>
          <li>
            <strong>Trading</strong>
            <span>Disabled in V1</span>
          </li>
        </ul>
      </section>
      <InstrumentVerification />
    </main>
  );
}
