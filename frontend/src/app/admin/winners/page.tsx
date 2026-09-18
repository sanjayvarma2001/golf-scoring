"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Winner } from "@/lib/types";

export default function AdminWinnersPage() {
  const [winners, setWinners] = useState<Winner[]>([]);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<Winner[]>("/winners").then(setWinners).catch(() => setError("Couldn't load winners."));
  }
  useEffect(load, []);

  async function verify(w: Winner, approve: boolean) {
    try {
      await api.post(`/winners/${w.id}/verify`, { approve });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Verification failed.");
    }
  }

  async function pay(w: Winner) {
    try {
      await api.post(`/winners/${w.id}/pay`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Payout failed.");
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Winners</h1>
      {error && <p className="mt-3 rounded-lg bg-amber/10 px-4 py-2 text-sm text-amber-light">{error}</p>}

      <div className="mt-6 space-y-3">
        {winners.length === 0 && <p className="text-cream/50">No winners yet.</p>}
        {winners.map((w) => (
          <div key={w.id} className="rounded-xl border border-border bg-surface p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-medium">
                  {w.match_tier}-number match &mdash; ${w.prize_amount.toFixed(2)}
                </p>
                <p className="mt-1 text-sm text-cream/50">
                  Verification: <span className="capitalize">{w.verification_status}</span> &middot; Payment:{" "}
                  <span className="capitalize">{w.payment_status}</span>
                </p>
                {w.proof_image_url ? (
                  <a href={w.proof_image_url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-sm text-sage-light hover:text-sage">
                    View proof &rarr;
                  </a>
                ) : (
                  <p className="mt-1 text-sm text-cream/40">No proof submitted yet</p>
                )}
              </div>
              <div className="flex gap-2">
                {w.verification_status === "pending" && (
                  <>
                    <button
                      onClick={() => verify(w, true)}
                      className="rounded-full bg-sage px-4 py-1.5 text-sm font-medium text-navy hover:bg-sage-light"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => verify(w, false)}
                      className="rounded-full border border-border px-4 py-1.5 text-sm hover:border-red-400 hover:text-red-300"
                    >
                      Reject
                    </button>
                  </>
                )}
                {w.verification_status === "approved" && w.payment_status === "pending" && (
                  <button
                    onClick={() => pay(w)}
                    className="rounded-full bg-amber px-4 py-1.5 text-sm font-medium text-navy hover:bg-amber-light"
                  >
                    Mark paid
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
