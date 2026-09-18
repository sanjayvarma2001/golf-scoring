"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import type { Charity } from "@/lib/types";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [charities, setCharities] = useState<Charity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    username: "",
    full_name: "",
    email: "",
    password: "",
    charity_id: "",
    charity_percentage: 10,
  });

  useEffect(() => {
    api
      .get<Charity[]>("/charities")
      .then((list) => {
        setCharities(list);
        if (list.length > 0) setForm((f) => ({ ...f, charity_id: list[0].id }));
      })
      .catch(() => setCharities([]));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.charity_id) {
      setError("Please select a charity to support.");
      return;
    }
    setSubmitting(true);
    try {
      await register(form);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong, please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg px-6 py-16">
      <h1 className="text-2xl font-semibold">Create your account</h1>
      <p className="mt-2 text-sm text-cream/60">
        Pick a charity now, you can increase your contribution or change plans anytime.
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm text-cream/70">Full name</label>
            <input
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm outline-none focus:border-sage"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-cream/70">Username</label>
            <input
              required
              minLength={3}
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm outline-none focus:border-sage"
            />
          </div>
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-cream/70">Email</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm outline-none focus:border-sage"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-cream/70">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm outline-none focus:border-sage"
          />
          <p className="mt-1 text-xs text-cream/45">At least 8 characters.</p>
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-cream/70">Charity you&apos;re supporting</label>
          <select
            required
            value={form.charity_id}
            onChange={(e) => setForm({ ...form, charity_id: e.target.value })}
            className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm outline-none focus:border-sage"
          >
            {charities.length === 0 && <option value="">No charities available yet</option>}
            {charities.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1.5 flex items-center justify-between text-sm text-cream/70">
            <span>Contribution percentage</span>
            <span className="text-amber-light">{form.charity_percentage}%</span>
          </label>
          <input
            type="range"
            min={10}
            max={100}
            step={5}
            value={form.charity_percentage}
            onChange={(e) => setForm({ ...form, charity_percentage: Number(e.target.value) })}
            className="w-full accent-amber"
          />
          <p className="mt-1 text-xs text-cream/45">Minimum 10% of your subscription, raise it anytime.</p>
        </div>

        {error && <p className="rounded-lg bg-amber/10 px-4 py-2 text-sm text-amber-light">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-full bg-amber py-2.5 font-medium text-navy transition-colors hover:bg-amber-light disabled:opacity-60"
        >
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-cream/60">
        Already have an account?{" "}
        <Link href="/login" className="text-sage-light hover:text-sage">
          Log in
        </Link>
      </p>
    </div>
  );
}
