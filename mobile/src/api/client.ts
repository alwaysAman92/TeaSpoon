import Constants from "expo-constants";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

import type {
  Dashboard,
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
  const userId = await getUserId();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": userId,
      ...(init.headers || {}),
    },
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

  preview(barcode: string): Promise<ScanResult> {
    return request<ScanResult>(`/scan/${encodeURIComponent(barcode)}`);
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
};
