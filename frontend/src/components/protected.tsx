"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

/**
 * Client-side route guard. Auth is a bearer token in localStorage (no
 * cookies/middleware), so protection has to happen after mount once we
 * know whether a user is loaded - this renders nothing until then to
 * avoid a flash of protected content.
 */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return <div className="mx-auto max-w-6xl px-6 py-24 text-center text-cream/50">Loading...</div>;
  }
  return <>{children}</>;
}

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) router.replace("/");
  }, [loading, user, router]);

  if (loading || !user || user.role !== "admin") {
    return <div className="mx-auto max-w-6xl px-6 py-24 text-center text-cream/50">Loading...</div>;
  }
  return <>{children}</>;
}
