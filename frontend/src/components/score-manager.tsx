"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Score } from "@/lib/types";

export default function ScoreManager({ initialScores }: { initialScores: Score[] }) {
  const [scores, setScores] = useState<Score[]>(initialScores);
  const [course, setCourse] = useState("");
  const [score, setScore] = useState(30);
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function resetForm() {
    setCourse("");
    setScore(30);
    setDate(new Date().toISOString().slice(0, 10));
    setEditingId(null);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (editingId) {
        const updated = await api.put<Score>(`/scores/${editingId}`, { course: course || null, score, date_played: date });
        setScores((prev) => prev.map((s) => (s.id === editingId ? updated : s)).sort((a, b) => (a.date_played < b.date_played ? 1 : -1)));
      } else {
        const created = await api.post<Score>("/scores", { course: course || null, score, date_played: date });
        setScores((prev) => {
          const next = [created, ...prev].sort((a, b) => (a.date_played < b.date_played ? 1 : -1));
          return next.slice(0, 5);
        });
      }
      resetForm();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save that score.");
    } finally {
      setSubmitting(false);
    }
  }

  async function onDelete(id: string) {
    try {
      await api.del(`/scores/${id}`);
      setScores((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't delete that score.");
    }
  }

  function onEdit(s: Score) {
    setEditingId(s.id);
    setCourse(s.course ?? "");
    setScore(s.score);
    setDate(s.date_played);
  }

  return (
    <div>
      <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-[1fr_auto_auto_auto] sm:items-end">
        <div>
          <label className="mb-1 block text-xs text-cream/60">Course (optional)</label>
          <input
            value={course}
            onChange={(e) => setCourse(e.target.value)}
            className="w-full rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
            placeholder="e.g. Riverbend"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-cream/60">Score (1-45)</label>
          <input
            type="number"
            min={1}
            max={45}
            required
            value={score}
            onChange={(e) => setScore(Number(e.target.value))}
            className="w-24 rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-cream/60">Date played</label>
          <input
            type="date"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          />
        </div>
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-full bg-sage px-5 py-2 text-sm font-medium text-navy transition-colors hover:bg-sage-light disabled:opacity-60"
          >
            {editingId ? "Save" : "Add score"}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="rounded-full border border-border px-4 py-2 text-sm text-cream/70 hover:text-cream"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {error && <p className="mt-3 rounded-lg bg-amber/10 px-4 py-2 text-sm text-amber-light">{error}</p>}

      <div className="mt-6 overflow-hidden rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-navy text-cream/60">
            <tr>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Course</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {scores.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-cream/45">
                  No scores yet - add your first round above.
                </td>
              </tr>
            )}
            {scores.map((s) => (
              <tr key={s.id} className="border-t border-border">
                <td className="px-4 py-3">{s.date_played}</td>
                <td className="px-4 py-3 text-cream/70">{s.course ?? "—"}</td>
                <td className="px-4 py-3 font-medium text-amber-light">{s.score}</td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => onEdit(s)} className="mr-3 text-sage-light hover:text-sage">
                    Edit
                  </button>
                  <button onClick={() => onDelete(s.id)} className="text-cream/50 hover:text-red-400">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-cream/40">Only your latest 5 scores are kept - a new entry replaces the oldest.</p>
    </div>
  );
}
