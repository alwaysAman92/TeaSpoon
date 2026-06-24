import Constants from "expo-constants";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

import type {
  Dashboard,
  LeaderboardEntry,
  ScanResult,
  Settings,
  TrendPoint,
} from "@/types";

// API base URL comes from app config (app.json -> extra.apiBaseUrl) or an
// EXPO_PUBLIC env var. Never hard-code production secrets in the client.
const BASE_URL: string =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined)?.apiBaseUrl ||
  "http://localhost:8000";

const USER_KEY = "teaspoon.userId";

// Clerk token getter — set by the auth bridge in App.tsx when Clerk is active.
let _getClerkToken: (() => Promise<string | null>) | null = null;

export function setClerkTokenGetter(getter: () => Promise<string | null>) {
  _getClerkToken = getter;
}

function newId(): string {
  return `u_${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
}

// In production this is a verified Clerk session id. For the MVP we issue an
// opaque random id once and persist it. Native uses the OS secure store (never
// AsyncStorage); the web preview falls back to localStorage.
async function getUserId(): Promise<string> {
  if (Platform.OS === "web") {
    try {
      let id = globalThis.localStorage?.getItem(USER_KEY);
      if (!id) {
        id = newId();
        globalThis.localStorage?.setItem(USER_KEY, id);
      }
      return id;
    } catch {
      return "web-demo-user";
    }
  }
  let id = await SecureStore.getItemAsync(USER_KEY);
  if (!id) {
    id = newId();
    await SecureStore.setItemAsync(USER_KEY, id);
  }
  return id;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> || {}),
  };

  // If Clerk is active, inject Bearer token. Otherwise fall back to X-User-Id.
  if (_getClerkToken) {
    const token = await _getClerkToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  } else {
    const userId = await getUserId();
    headers["X-User-Id"] = userId;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  baseUrl: BASE_URL,

  scan(barcode: string, opts: { servings?: number; log?: boolean } = {}): Promise<ScanResult> {
    return request<ScanResult>("/scan", {
      method: "POST",
      body: JSON.stringify({ barcode, servings: opts.servings ?? 1, log: opts.log ?? true }),
    });
  },

  preview(barcode: string, date?: string): Promise<ScanResult> {
    const qs = date ? `?date=${encodeURIComponent(date)}` : "";
    return request<ScanResult>(`/scan/${encodeURIComponent(barcode)}${qs}`);
  },

  dashboard(date?: string): Promise<Dashboard> {
    return request<Dashboard>(date ? `/dashboard?date=${encodeURIComponent(date)}` : "/dashboard");
  },

  trend(days = 7): Promise<TrendPoint[]> {
    return request<TrendPoint[]>(`/dashboard/trend?days=${days}`);
  },

  getSettings(): Promise<Settings> {
    return request<Settings>("/settings");
  },

  updateSettings(patch: Partial<Settings>): Promise<Settings> {
    return request<Settings>("/settings", {
      method: "PUT",
      body: JSON.stringify(patch),
    });
  },

  reportData(barcode: string, reason: string): Promise<unknown> {
    return request("/products/report", {
      method: "POST",
      body: JSON.stringify({ barcode, reason }),
    });
  },

  async submitContribution(barcode: string, photoUri: string): Promise<unknown> {
    const formData = new FormData();
    formData.append("barcode", barcode);
    formData.append("photo", {
      uri: photoUri,
      name: "label.jpg",
      type: "image/jpeg",
    } as unknown as Blob);

    const headers: Record<string, string> = {};
    if (_getClerkToken) {
      const token = await _getClerkToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    } else {
      const userId = await getUserId();
      headers["X-User-Id"] = userId;
    }

    const res = await fetch(`${BASE_URL}/contributions/submit`, {
      method: "POST",
      body: formData,
      headers,
    });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    return res.json();
  },

  getLeaderboard(params?: { city?: string; region?: string }): Promise<LeaderboardEntry[]> {
    const qs = new URLSearchParams();
    if (params?.city) qs.set("city", params.city);
    if (params?.region) qs.set("region", params.region);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<LeaderboardEntry[]>(`/contributions/leaderboard${suffix}`);
  },
};
