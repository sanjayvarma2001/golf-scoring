"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Draw, DrawSimulationResult } from "@/lib/types";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function AdminDrawsPage() {
  const [draws, setDraws] = useState<Draw[]>([]);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [drawType, setDrawType] = useState<"random" | "algorithmic">("random");
  const [error, setError] = useState<string | null>(null);
  const [simResults, setSimResults] = useState<Record<string, DrawSimulationResult>>({});
  const [busy, setBusy] = useState<string | null>(null);

  function load() {
    api.get<Draw[]>("/draws").then(setDraws).catch(() => setError("Couldn't load draws."));
  }
  useEffect(load, []);

  async function createDraw(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post<Draw>("/draws", { month, year, draw_type: drawType });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create draw.");
    }
  }

  async function simulate(id: string) {
    setBusy(id);
    setError(null);
    try {
      const result = await api.post<DrawSimulationResult>(`/draws/${id}/simulate`);
      setSimResults((prev) => ({ ...prev, [id]: result }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Simulation failed.");
    } finally {
      setBusy(null);
    }
  }

  async function publish(id: string) {
    if (!confirm("Publish this draw? Winners will be finalized and visible to subscribers.")) return;
    setBusy(id);
    setError(null);
    try {
      await api.post(`/draws/${id}/publish`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Publish failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Draws</h1>

      <form onSubmit={createDraw} className="mt-6 flex flex-wrap items-end gap-3 rounded-xl border border-border bg-surface p-5">
        <div>
          <label className="mb-1 block text-xs text-cream/60">Month</label>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          >
            {MONTHS.map((m, i) => (
              <option key={m} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-cream/60">Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24 rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-cream/60">Draw logic</label>
          <select
            value={drawType}
            onChange={(e) => setDrawType(e.target.value as "random" | "algorithmic")}
            className="rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          >
            <option value="random">Random (lottery-style)</option>
            <option value="algorithmic">Algorithmic (weighted by score)</option>
          </select>
        </div>
        <button type="submit" className="rounded-full bg-amber px-5 py-2 text-sm font-medium text-navy hover:bg-amber-light">
          Create draw
        </button>
      </form>

      {error && <p className="mt-4 rounded-lg bg-amber/10 px-4 py-2 text-sm text-amber-light">{error}</p>}

      <div className="mt-6 space-y-4">
        {draws.map((d) => {
          const sim = simResults[d.id];
          return (
            <div key={d.id} className="rounded-xl border border-border bg-surface p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="font-medium">
                    {MONTHS[d.month - 1]} {d.year} &middot; <span className="capitalize text-cream/60">{d.draw_type}</span>
                  </h3>
                  <p className="mt-1 text-sm text-cream/50 capitalize">
                    {d.status} {d.winning_numbers && `- winning numbers: ${d.winning_numbers.join(", ")}`}
                  </p>
                </div>
                {d.status !== "published" && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => simulate(d.id)}
                      disabled={busy === d.id}
                      className="rounded-full border border-border px-4 py-1.5 text-sm hover:border-sage disabled:opacity-50"
                    >
                      Simulate
                    </button>
                    <button
                      onClick={() => publish(d.id)}
                      disabled={busy === d.id}
                      className="rounded-full bg-amber px-4 py-1.5 text-sm font-medium text-navy hover:bg-amber-light disabled:opacity-50"
                    >
                      Publish
                    </button>
                  </div>
                )}
              </div>

              {sim && (
                <div className="mt-4 rounded-lg bg-navy p-4 text-sm">
                  <p className="text-cream/60">
                    Simulated winning numbers: <span className="text-amber-light">{sim.winning_numbers.join(", ")}</span> &middot;{" "}
                    {sim.total_participants} participants
                  </p>
                  <div className="mt-2 grid gap-2 sm:grid-cols-3">
                    {sim.tiers.map((t) => (
                      <div key={t.match_tier} className="rounded-lg border border-border px-3 py-2">
                        <p className="font-medium">{t.match_tier}-match</p>
                        <p className="text-cream/60">
                          {t.winner_count} winner(s) &middot; ${t.prize_per_winner.toFixed(2)} each
                        </p>
                      </div>
                    ))}
                  </div>
                  {sim.jackpot_rolled_over && <p className="mt-2 text-amber-light">Jackpot would roll over.</p>}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
