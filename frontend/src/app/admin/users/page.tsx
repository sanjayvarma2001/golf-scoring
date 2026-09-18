"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AdminUser } from "@/lib/types";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<AdminUser[]>("/admin/users").then(setUsers).catch(() => setError("Couldn't load users."));
  }

  useEffect(load, []);

  async function toggleActive(u: AdminUser) {
    try {
      const updated = await api.put<AdminUser>(`/admin/users/${u.id}`, { is_active: !u.is_active });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? updated : x)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    }
  }

  async function toggleRole(u: AdminUser) {
    try {
      const updated = await api.put<AdminUser>(`/admin/users/${u.id}`, {
        role: u.role === "admin" ? "subscriber" : "admin",
      });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? updated : x)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    }
  }

  async function remove(u: AdminUser) {
    if (!confirm(`Delete ${u.username}? This can't be undone.`)) return;
    try {
      await api.del(`/admin/users/${u.id}`);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold">Users</h1>
      {error && <p className="mt-3 rounded-lg bg-amber/10 px-4 py-2 text-sm text-amber-light">{error}</p>}

      <div className="mt-6 overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface text-cream/60">
            <tr>
              <th className="px-4 py-3 font-medium">Username</th>
              <th className="px-4 py-3 font-medium">Email</th>
              <th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-border">
                <td className="px-4 py-3">{u.username}</td>
                <td className="px-4 py-3 text-cream/70">{u.email}</td>
                <td className="px-4 py-3 capitalize">{u.role}</td>
                <td className="px-4 py-3">{u.is_active ? "Active" : "Deactivated"}</td>
                <td className="px-4 py-3 text-right space-x-3">
                  <button onClick={() => toggleRole(u)} className="text-sage-light hover:text-sage">
                    Make {u.role === "admin" ? "subscriber" : "admin"}
                  </button>
                  <button onClick={() => toggleActive(u)} className="text-amber-light hover:text-amber">
                    {u.is_active ? "Deactivate" : "Activate"}
                  </button>
                  <button onClick={() => remove(u)} className="text-cream/50 hover:text-red-400">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
