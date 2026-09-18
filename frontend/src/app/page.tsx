import Link from "next/link";
import type { Charity } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8010/api/v1";

async function getFeaturedCharities(): Promise<Charity[]> {
  try {
    const res = await fetch(`${API_URL}/charities?featured_only=true`, { cache: "no-store" });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function LandingPage() {
  const charities = await getFeaturedCharities();

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full bg-sage/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-24 h-96 w-96 rounded-full bg-amber/10 blur-3xl" />
        <div className="relative mx-auto max-w-6xl px-6 py-24 md:py-32">
          <p className="mb-4 text-sm font-medium uppercase tracking-widest text-sage-light">
            Golf performance &middot; monthly draws &middot; real charity impact
          </p>
          <h1 className="max-w-3xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
            Play your round. Back a cause. Win something real.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-cream/70">
            Log your last five Stableford scores, get entered into a monthly prize draw, and
            send a share of every subscription straight to a charity you pick. No fairway
            clichés, just your game and your impact, in one place.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              href="/register"
              className="rounded-full bg-amber px-7 py-3 text-base font-medium text-navy transition-transform hover:scale-[1.03] hover:bg-amber-light"
            >
              Subscribe and start scoring
            </Link>
            <Link href="/charities" className="text-base text-cream/80 underline underline-offset-4 hover:text-cream">
              Browse charities first
            </Link>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="text-2xl font-semibold">How it works</h2>
        <div className="mt-10 grid gap-6 md:grid-cols-4">
          {[
            { step: "01", title: "Subscribe", body: "Pick a monthly or yearly plan. A minimum of 10% goes straight to your chosen charity." },
            { step: "02", title: "Score", body: "Log your last five Stableford rounds. We keep the latest five, always in order." },
            { step: "03", title: "Enter the draw", body: "Every active subscriber gets a monthly ticket. Match 3, 4, or 5 numbers to win a share of the pool." },
            { step: "04", title: "Give and get paid", body: "Verified winners get paid out, and your charity keeps getting a cut every month you're subscribed." },
          ].map((s) => (
            <div key={s.step} className="rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-sage/40">
              <span className="text-sm font-mono text-amber-light">{s.step}</span>
              <h3 className="mt-3 text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-cream/65">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Prize pool teaser */}
      <section className="border-y border-border bg-surface/60">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="text-2xl font-semibold">Where the prize pool goes</h2>
          <p className="mt-3 max-w-2xl text-cream/65">
            A fixed share of the monthly pool is split automatically across three match tiers.
            An unclaimed 5-match jackpot rolls straight into next month.
          </p>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {[
              { tier: "5-number match", share: "40%", note: "Jackpot - rolls over if unclaimed" },
              { tier: "4-number match", share: "35%", note: "Split equally among winners" },
              { tier: "3-number match", share: "25%", note: "Split equally among winners" },
            ].map((p) => (
              <div key={p.tier} className="rounded-2xl border border-border bg-navy p-6">
                <div className="text-3xl font-semibold text-amber-light">{p.share}</div>
                <div className="mt-2 font-medium">{p.tier}</div>
                <div className="mt-1 text-sm text-cream/55">{p.note}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Charity spotlight */}
      {charities.length > 0 && (
        <section className="mx-auto max-w-6xl px-6 py-20">
          <div className="flex items-end justify-between">
            <h2 className="text-2xl font-semibold">Featured charities</h2>
            <Link href="/charities" className="text-sm text-sage-light hover:text-sage">
              View directory &rarr;
            </Link>
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            {charities.slice(0, 4).map((c) => (
              <Link
                key={c.id}
                href={`/charities/${c.id}`}
                className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-amber/40"
              >
                <h3 className="text-lg font-semibold group-hover:text-amber-light">{c.name}</h3>
                <p className="mt-2 line-clamp-2 text-sm text-cream/65">{c.description}</p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Final CTA */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <div className="rounded-3xl border border-border bg-gradient-to-br from-sage/15 to-amber/10 p-12 text-center">
          <h2 className="text-3xl font-semibold">Your round can do more than lower your handicap.</h2>
          <p className="mx-auto mt-4 max-w-xl text-cream/70">
            Join for the price of a round of golf a month, and turn every score you post into
            support for a cause you care about.
          </p>
          <Link
            href="/register"
            className="mt-8 inline-block rounded-full bg-amber px-7 py-3 font-medium text-navy transition-transform hover:scale-[1.03] hover:bg-amber-light"
          >
            Get started
          </Link>
        </div>
      </section>
    </div>
  );
}
