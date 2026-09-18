import Link from "next/link";
import { notFound } from "next/navigation";
import type { Charity } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8010/api/v1";

async function getCharity(id: string): Promise<Charity | null> {
  try {
    const res = await fetch(`${API_URL}/charities/${id}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function CharityProfilePage({ params }: PageProps<"/charities/[id]">) {
  const { id } = await params;
  const charity = await getCharity(id);
  if (!charity) notFound();

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <Link href="/charities" className="text-sm text-sage-light hover:text-sage">
        &larr; Back to directory
      </Link>

      <div className="mt-6 flex items-start justify-between gap-6">
        <h1 className="text-3xl font-semibold">{charity.name}</h1>
        {charity.is_featured && (
          <span className="mt-1 shrink-0 rounded-full bg-amber/15 px-3 py-1 text-xs font-medium text-amber-light">
            Featured
          </span>
        )}
      </div>

      {charity.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={charity.image_url}
          alt={charity.name}
          className="mt-6 h-64 w-full rounded-2xl object-cover"
          onError={(e) => ((e.target as HTMLImageElement).style.display = "none")}
        />
      )}

      <p className="mt-6 whitespace-pre-line text-cream/75">{charity.description}</p>

      {charity.website_url && (
        <a
          href={charity.website_url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-block text-sm text-sage-light underline underline-offset-4 hover:text-sage"
        >
          Visit website &rarr;
        </a>
      )}

      {charity.events.length > 0 && (
        <div className="mt-12">
          <h2 className="text-xl font-semibold">Upcoming events</h2>
          <div className="mt-4 space-y-4">
            {charity.events.map((e) => (
              <div key={e.id} className="rounded-xl border border-border bg-surface p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-medium">{e.title}</h3>
                  <span className="text-sm text-amber-light">
                    {new Date(e.event_date).toLocaleDateString(undefined, { dateStyle: "medium" })}
                  </span>
                </div>
                {e.location && <p className="mt-1 text-sm text-cream/55">{e.location}</p>}
                {e.description && <p className="mt-2 text-sm text-cream/65">{e.description}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-12 rounded-2xl border border-border bg-gradient-to-br from-sage/15 to-amber/10 p-8 text-center">
        <p className="text-cream/75">Want to support {charity.name} through your golf?</p>
        <Link
          href="/register"
          className="mt-4 inline-block rounded-full bg-amber px-6 py-2.5 font-medium text-navy hover:bg-amber-light"
        >
          Subscribe and select them
        </Link>
      </div>
    </div>
  );
}
