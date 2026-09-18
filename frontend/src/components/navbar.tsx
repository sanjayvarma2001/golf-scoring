"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const link = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-sm transition-colors hover:text-amber-light ${
        pathname === href ? "text-cream font-medium" : "text-cream/70"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-navy/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight">
          digital<span className="text-sage-light">.</span>HEROES
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {link("/charities", "Charities")}
          {user && link("/dashboard", "Dashboard")}
          {user?.role === "admin" && link("/admin", "Admin")}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <button
              onClick={() => {
                logout();
                router.push("/");
              }}
              className="rounded-full border border-border px-4 py-1.5 text-sm text-cream/80 transition-colors hover:border-cream/40 hover:text-cream"
            >
              Log out
            </button>
          ) : (
            <>
              <Link href="/login" className="text-sm text-cream/80 hover:text-cream">
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-amber px-4 py-1.5 text-sm font-medium text-navy transition-colors hover:bg-amber-light"
              >
                Subscribe
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
