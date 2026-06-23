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

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(true);

  const refreshSettings = useCallback(async () => {
    try {
      const next = await api.getSettings();
      setSettings(next);
    } catch {
      // Offline / backend down: fall back to sensible defaults.
      setSettings((prev) => prev ?? DEFAULT_SETTINGS);
    } finally {
      setLoadingSettings(false);
    }
  }, []);

  const saveSettings = useCallback(async (patch: Partial<Settings>) => {
    // Optimistic update so the toggle feels instant.
    setSettings((prev) => ({ ...(prev ?? DEFAULT_SETTINGS), ...patch }));
    try {
      const next = await api.updateSettings(patch);
      setSettings(next);
    } catch {
      // Keep the optimistic value; a later refresh reconciles.
    }
  }, []);

  useEffect(() => {
    void refreshSettings();
  }, [refreshSettings]);

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
