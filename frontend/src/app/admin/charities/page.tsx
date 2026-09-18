"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Charity } from "@/lib/types";

const emptyForm = { name: "", description: "", website_url: "", image_url: "", is_featured: false };

export default function AdminCharitiesPage() {
  const [charities, setCharities] = useState<Charity[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<Charity[]>("/charities").then(setCharities);
  }
  useEffect(load, []);

  async function createCharity(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/charities", form);
      setForm(emptyForm);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create charity.");
    }
  }

  async function toggleFeatured(c: Charity) {
    await api.put(`/charities/${c.id}`, { is_featured: !c.is_featured });
    load();
  }

  async function remove(c: Charity) {
    if (!confirm(`Delete ${c.name}?`)) return;
    try {
      await api.del(`/charities/${c.id}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed - charity may still have subscribers linked to it.");
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Charities</h1>

      <form onSubmit={createCharity} className="mt-6 space-y-3 rounded-xl border border-border bg-surface p-5">
        <h2 className="text-sm font-medium text-cream/70">Add a new charity</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            required
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          />
          <input
            placeholder="Website URL"
            value={form.website_url}
            onChange={(e) => setForm({ ...form, website_url: e.target.value })}
            className="rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
          />
        </div>
        <textarea
          required
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          rows={3}
          className="w-full rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
        />
        <input
          placeholder="Image URL"
          value={form.image_url}
          onChange={(e) => setForm({ ...form, image_url: e.target.value })}
          className="w-full rounded-lg border border-border bg-navy px-3 py-2 text-sm outline-none focus:border-sage"
        />
        <label className="flex items-center gap-2 text-sm text-cream/70">
          <input
            type="checkbox"
            checked={form.is_featured}
            onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
          />
          Feature on homepage
        </label>
        <button type="submit" className="rounded-full bg-amber px-5 py-2 text-sm font-medium text-navy hover:bg-amber-light">
          Add charity
        </button>
      </form>

      {error && <p className="mt-4 rounded-lg bg-amber/10 px-4 py-2 text-sm text-amber-light">{error}</p>}

      <div className="mt-6 space-y-3">
        {charities.map((c) => (
          <div key={c.id} className="flex items-center justify-between rounded-xl border border-border bg-surface p-4">
            <div>
              <p className="font-medium">{c.name}</p>
              <p className="text-sm text-cream/50">{c.is_featured ? "Featured" : "Not featured"}</p>
            </div>
            <div className="flex gap-3 text-sm">
              <button onClick={() => toggleFeatured(c)} className="text-sage-light hover:text-sage">
                {c.is_featured ? "Unfeature" : "Feature"}
              </button>
              <button onClick={() => remove(c)} className="text-cream/50 hover:text-red-400">
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
