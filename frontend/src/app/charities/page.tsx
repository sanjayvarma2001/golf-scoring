"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Charity } from "@/lib/types";

export default function CharitiesPage() {
  const [charities, setCharities] = useState<Charity[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handle = setTimeout(() => {
      setLoading(true);
      const qs = search ? `?search=${encodeURIComponent(search)}` : "";
      api
        .get<Charity[]>(`/charities${qs}`)
        .then(setCharities)
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(handle);
  }, [search]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="text-3xl font-semibold">Charity directory</h1>
      <p className="mt-2 max-w-xl text-cream/65">
        Every subscriber directs part of their fee to a cause of their choice. Browse who&apos;s
        on the platform and what they do.
      </p>

      <input
        placeholder="Search charities..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mt-8 w-full max-w-sm rounded-lg border border-border bg-surface px-4 py-2.5 text-sm outline-none focus:border-sage"
      />

      {loading ? (
        <p className="mt-10 text-cream/50">Loading charities...</p>
      ) : charities.length === 0 ? (
        <p className="mt-10 text-cream/50">No charities match your search.</p>
      ) : (
        <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {charities.map((c) => (
            <Link
              key={c.id}
              href={`/charities/${c.id}`}
              className="group flex flex-col rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-amber/40"
            >
              {c.is_featured && (
                <span className="mb-3 w-fit rounded-full bg-amber/15 px-3 py-1 text-xs font-medium text-amber-light">
                  Featured
                </span>
              )}
              <h3 className="text-lg font-semibold group-hover:text-amber-light">{c.name}</h3>
              <p className="mt-2 line-clamp-3 flex-1 text-sm text-cream/65">{c.description}</p>
              {c.events.length > 0 && (
                <p className="mt-3 text-xs text-sage-light">{c.events.length} upcoming event(s)</p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
