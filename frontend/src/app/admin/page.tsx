"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReportsSummary } from "@/lib/types";

export default function AdminOverviewPage() {
  const [reports, setReports] = useState<ReportsSummary | null>(null);

  useEffect(() => {
    api.get<ReportsSummary>("/admin/reports").then(setReports);
  }, []);

  const cards = reports
    ? [
        { label: "Total users", value: reports.total_users },
        { label: "Active subscribers", value: reports.active_subscribers },
        { label: "Prize pool paid", value: `$${reports.total_prize_pool_paid.toFixed(2)}` },
        { label: "Prize pool pending", value: `$${reports.total_prize_pool_pending.toFixed(2)}` },
        { label: "Charity contributions", value: `$${reports.charity_contribution_total.toFixed(2)}` },
        { label: "Draws published", value: reports.total_draws_published },
        { label: "Total winners", value: reports.total_winners },
      ]
    : [];

  return (
    <div>
      <h1 className="text-2xl font-semibold">Reports &amp; analytics</h1>
      <p className="mt-2 text-sm text-cream/60">A snapshot of the whole platform.</p>

      {!reports ? (
        <p className="mt-8 text-cream/50">Loading...</p>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((c) => (
            <div key={c.label} className="rounded-2xl border border-border bg-surface p-6">
              <p className="text-2xl font-semibold text-amber-light">{c.value}</p>
              <p className="mt-1 text-sm text-cream/60">{c.label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
