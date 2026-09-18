"use client";

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { api, getToken, setToken } from "./api";
import type { TokenResponse, UserPublic } from "./types";

interface AuthContextValue {
  user: UserPublic | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<UserPublic>;
  register: (payload: {
    username: string;
    full_name: string;
    email: string;
    password: string;
    charity_id: string;
    charity_percentage: number;
  }) => Promise<UserPublic>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<UserPublic>("/users/me");
      setUser(me);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Intentional mount-time check of localStorage for an existing session.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  const login = async (username: string, password: string) => {
    const data = await api.post<TokenResponse>("/auth/login", { username, password });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register: AuthContextValue["register"] = async (payload) => {
    const data = await api.post<TokenResponse>("/auth/register", payload);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
