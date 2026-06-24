import { useAuth } from "@clerk/clerk-expo";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/api/client";
import type { Settings } from "@/types";

interface AppState {
  settings: Settings | null;
  loadingSettings: boolean;
  refreshSettings: () => Promise<void>;
  saveSettings: (patch: Partial<Settings>) => Promise<void>;
}

const DEFAULT_SETTINGS: Settings = {
  alternatives_priority: "healthier",
  primary_nutrient: "sugar",
  health_flags: [],
  target_sugar_tsp: null,
  target_sodium_mg: null,
  target_protein_g: null,
  points: 0,
  city: null,
  region: null,
  badges: [],
};

const AppContext = createContext<AppState | undefined>(undefined);

const CLERK_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;
const useClerkAuth = CLERK_KEY
  ? useAuth
  : () => ({ isSignedIn: false, getToken: async () => null });

export function AppProvider({ children }: { children: React.ReactNode }) {
  const { isSignedIn } = useClerkAuth();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [pendingSettings, setPendingSettings] = useState<Partial<Settings> | null>(null);

  const saveSettings = useCallback(async (patch: Partial<Settings>) => {
    if (!isSignedIn) {
      // Save onboarding choices to pending settings while logged out
      setPendingSettings((prev) => ({ ...prev, ...patch }));
      setSettings((prev) => ({ ...(prev ?? DEFAULT_SETTINGS), ...patch }));
      return;
    }

    // Optimistic update for authenticated user
    setSettings((prev) => ({ ...(prev ?? DEFAULT_SETTINGS), ...patch }));
    try {
      const next = await api.updateSettings(patch);
      setSettings(next);
    } catch {
      // Keep optimistic value; a later refresh reconciles
    }
  }, [isSignedIn]);

  const refreshSettings = useCallback(async () => {
    try {
      let next = await api.getSettings();
      // If we have pending onboarding settings, sync them now that we are authenticated
      if (isSignedIn && pendingSettings && Object.keys(pendingSettings).length > 0) {
        next = await api.updateSettings(pendingSettings);
        setPendingSettings(null);
      }
      setSettings(next);
    } catch {
      // Offline / backend down: fall back to sensible defaults.
      setSettings((prev) => prev ?? DEFAULT_SETTINGS);
    } finally {
      setLoadingSettings(false);
    }
  }, [isSignedIn, pendingSettings]);

  useEffect(() => {
    void refreshSettings();
  }, [isSignedIn, refreshSettings]);

  const value = useMemo<AppState>(
    () => ({ settings, loadingSettings, refreshSettings, saveSettings }),
    [settings, loadingSettings, refreshSettings, saveSettings],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}

