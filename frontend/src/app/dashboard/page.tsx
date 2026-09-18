"use client";

import { useEffect, useState } from "react";
import { RequireAuth } from "@/components/protected";
import { api, ApiError } from "@/lib/api";
import type { UserDashboard, Winner } from "@/lib/types";
import ScoreManager from "@/components/score-manager";

function WinnerRow({ winner, onUpdate }: { winner: Winner; onUpdate: () => void }) {
  const [proofUrl, setProofUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submitProof() {
    if (!proofUrl.trim()) return;
    setSubmitting(true);
    try {
      await api.post(`/winners/${winner.id}/proof`, { proof_image_url: proofUrl.trim() });
      onUpdate();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-lg border border-border px-4 py-3 text-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span>
          {winner.match_tier}-number match &mdash; ${winner.prize_amount.toFixed(2)}
        </span>
        <span className="text-cream/50 capitalize">
          {winner.verification_status} &middot; {winner.payment_status}
        </span>
      </div>
      {!winner.proof_image_url && winner.verification_status === "pending" && (
        <div className="mt-2 flex gap-2">
          <input
            placeholder="Link to a screenshot of your scores"
            value={proofUrl}
            onChange={(e) => setProofUrl(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-navy px-3 py-1.5 text-xs outline-none focus:border-sage"
          />
          <button
            onClick={submitProof}
            disabled={submitting}
            className="rounded-full bg-sage px-4 py-1.5 text-xs font-medium text-navy hover:bg-sage-light disabled:opacity-60"
          >
            Submit proof
          </button>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-sage/20 text-sage-light",
    inactive: "bg-cream/10 text-cream/60",
    cancelled: "bg-amber/20 text-amber-light",
    lapsed: "bg-red-500/20 text-red-300",
  };
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${styles[status] ?? styles.inactive}`}>
      {status}
    </span>
  );
}

function DashboardContent() {
  const [data, setData] = useState<UserDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subscribing, setSubscribing] = useState<string | null>(null);

  async function load() {
    try {
      const d = await api.get<UserDashboard>("/users/me/dashboard");
      setData(d);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your dashboard.");
    }
  }

  useEffect(() => {
    // Intentional mount-time fetch, not a derived-state sync - the lint
    // rule's suggested alternatives (data-fetching libs/Suspense) are out
    // of scope for this app's size.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  async function subscribe(plan: "monthly" | "yearly") {
    setSubscribing(plan);
    try {
      await api.post("/subscriptions/checkout", { plan });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start your subscription.");
    } finally {
      setSubscribing(null);
    }
  }

  if (error) return <p className="mx-auto max-w-6xl px-6 py-16 text-amber-light">{error}</p>;
  if (!data) return <p className="mx-auto max-w-6xl px-6 py-16 text-cream/50">Loading your dashboard...</p>;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl font-semibold">Your dashboard</h1>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        {/* Subscription */}
        <div className="rounded-2xl border border-border bg-surface p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Subscription</h2>
            <StatusBadge status={data.subscription.status} />
          </div>
          {data.subscription.status === "active" ? (
            <div className="mt-4 space-y-1 text-sm text-cream/70">
              <p>
                Plan: <span className="text-cream">{data.subscription.plan}</span>
              </p>
              <p>
                Renews: <span className="text-cream">{data.subscription.renewal_date}</span>
              </p>
            </div>
          ) : (
            <div className="mt-4 space-y-2">
              <p className="text-sm text-cream/60">You don&apos;t have an active plan yet.</p>
              <div className="flex gap-2">
                <button
                  onClick={() => subscribe("monthly")}
                  disabled={!!subscribing}
                  className="rounded-full bg-amber px-4 py-2 text-sm font-medium text-navy hover:bg-amber-light disabled:opacity-60"
                >
                  {subscribing === "monthly" ? "Starting..." : "Go monthly"}
                </button>
                <button
                  onClick={() => subscribe("yearly")}
                  disabled={!!subscribing}
                  className="rounded-full border border-border px-4 py-2 text-sm text-cream/80 hover:border-sage disabled:opacity-60"
                >
                  {subscribing === "yearly" ? "Starting..." : "Go yearly"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Charity */}
        <div className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="font-semibold">Your charity</h2>
          {data.charity ? (
            <>
              <p className="mt-4 text-lg text-amber-light">{data.charity.name}</p>
              <p className="mt-1 text-sm text-cream/60">{data.charity_percentage}% of your subscription</p>
            </>
          ) : (
            <p className="mt-4 text-sm text-cream/60">No charity selected.</p>
          )}
        </div>

        {/* Participation */}
        <div className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="font-semibold">Participation</h2>
          <p className="mt-4 text-3xl font-semibold text-sage-light">{data.participation.draws_entered}</p>
          <p className="text-sm text-cream/60">Draws entered</p>
          {data.participation.upcoming_draw && (
            <p className="mt-3 text-sm text-cream/70">Next draw: {data.participation.upcoming_draw}</p>
          )}
        </div>
      </div>

      {/* Winnings */}
      <div className="mt-6 rounded-2xl border border-border bg-surface p-6">
        <h2 className="font-semibold">Winnings</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-2xl font-semibold text-amber-light">${data.winnings.total_won.toFixed(2)}</p>
            <p className="text-sm text-cream/60">Total won</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-sage-light">${data.winnings.total_paid.toFixed(2)}</p>
            <p className="text-sm text-cream/60">Paid out</p>
          </div>
          <div>
            <p className="text-2xl font-semibold">${data.winnings.total_pending.toFixed(2)}</p>
            <p className="text-sm text-cream/60">Pending</p>
          </div>
        </div>
        {data.winnings.winners.length > 0 && (
          <div className="mt-6 space-y-2">
            {data.winnings.winners.map((w) => (
              <WinnerRow key={w.id} winner={w} onUpdate={load} />
            ))}
          </div>
        )}
      </div>

      {/* Scores */}
      <div className="mt-6 rounded-2xl border border-border bg-surface p-6">
        <h2 className="font-semibold">Your scores</h2>
        <div className="mt-4">
          <ScoreManager initialScores={data.scores} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}
