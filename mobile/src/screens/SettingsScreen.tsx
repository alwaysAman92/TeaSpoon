import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/api/client";
import { Chip } from "@/components/Chip";
import { useApp } from "@/store/AppContext";
import type { LeaderboardEntry } from "@/types";
import { colors, font, radius, shadow, space, weight } from "@/theme";

const PRIMARY_NUTRIENTS = [
  { key: "sugar", label: "Sugar" },
  { key: "sodium", label: "Sodium" },
  { key: "protein", label: "Protein" },
  { key: "saturated_fat", label: "Sat fat" },
];

const HEALTH_FLAGS = [
  { key: "diabetic", label: "Diabetic" },
  { key: "hypertensive", label: "Hypertensive" },
  { key: "weight_goal", label: "Weight goal" },
  { key: "allergy", label: "Allergy" },
];

export function SettingsScreen() {
  const insets = useSafeAreaInsets();
  const { settings, saveSettings } = useApp();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [lbLoading, setLbLoading] = useState(false);
  const [lbScope, setLbScope] = useState<"national" | "local">("national");
  const [cityDraft, setCityDraft] = useState("");
  const [regionDraft, setRegionDraft] = useState("");

  useEffect(() => {
    if (settings) {
      setCityDraft(settings.city ?? "");
      setRegionDraft(settings.region ?? "");
    }
  }, [settings?.city, settings?.region]);

  const fetchLeaderboard = useCallback(async () => {
    setLbLoading(true);
    try {
      const params = lbScope === "local" && settings?.city ? { city: settings.city } : undefined;
      setLeaderboard(await api.getLeaderboard(params));
    } catch {
      /* best effort */
    } finally {
      setLbLoading(false);
    }
  }, [lbScope, settings?.city]);

  useEffect(() => {
    void fetchLeaderboard();
  }, [fetchLeaderboard]);

  if (!settings) {
    return <View style={styles.screen} />;
  }

  const toggleFlag = (flag: string) => {
    const has = settings.health_flags.includes(flag);
    const next = has
      ? settings.health_flags.filter((f) => f !== flag)
      : [...settings.health_flags, flag];
    void saveSettings({ health_flags: next });
  };

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={{ paddingTop: insets.top + space.lg, paddingBottom: 130, paddingHorizontal: space.lg }}
    >
      <Text style={styles.title}>Settings</Text>

      <Block label="What should we suggest?" hint="Re-ranks future scans only, not past history.">
        <View style={styles.toggle}>
          <Chip
            label="Healthier"
            tone={settings.alternatives_priority === "healthier" ? "warn" : "neutral"}
            active={settings.alternatives_priority === "healthier"}
            onPress={() => saveSettings({ alternatives_priority: "healthier" })}
          />
          <Chip
            label="Cheaper"
            tone={settings.alternatives_priority === "cheaper" ? "warn" : "neutral"}
            active={settings.alternatives_priority === "cheaper"}
            onPress={() => saveSettings({ alternatives_priority: "cheaper" })}
          />
        </View>
      </Block>

      <Block label="Track this on your dashboard">
        <View style={styles.toggle}>
          {PRIMARY_NUTRIENTS.map((n) => (
            <Chip
              key={n.key}
              label={n.label}
              tone={settings.primary_nutrient === n.key ? "warn" : "neutral"}
              active={settings.primary_nutrient === n.key}
              onPress={() => saveSettings({ primary_nutrient: n.key })}
            />
          ))}
        </View>
      </Block>

      <Block
        label="Health profile"
        hint="Tightens your daily limits — diabetic caps sugar at 6 tsp, hypertensive caps sodium at 1500 mg. Allergy enables allergen warnings on scan results."
      >
        <View style={styles.toggle}>
          {HEALTH_FLAGS.map((f) => (
            <Chip
              key={f.key}
              label={f.label}
              tone={settings.health_flags.includes(f.key) ? "good" : "neutral"}
              active={settings.health_flags.includes(f.key)}
              onPress={() => toggleFlag(f.key)}
            />
          ))}
        </View>
      </Block>

      {/* Location */}
      <Block label="Your location" hint="Used for the local leaderboard.">
        <TextInput
          style={styles.textInput}
          value={cityDraft}
          onChangeText={setCityDraft}
          placeholder="City (e.g. Mumbai)"
          placeholderTextColor={colors.inkFaint}
          onBlur={() => {
            if (cityDraft !== (settings.city ?? "")) {
              void saveSettings({ city: cityDraft } as Partial<typeof settings>);
            }
          }}
        />
        <TextInput
          style={[styles.textInput, { marginTop: space.sm }]}
          value={regionDraft}
          onChangeText={setRegionDraft}
          placeholder="Region (e.g. Maharashtra)"
          placeholderTextColor={colors.inkFaint}
          onBlur={() => {
            if (regionDraft !== (settings.region ?? "")) {
              void saveSettings({ region: regionDraft } as Partial<typeof settings>);
            }
          }}
        />
      </Block>

      {/* Contributor Recognition */}
      <Block label="Your contributions">
        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{settings.points}</Text>
            <Text style={styles.statLabel}>Points</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{settings.badges.length}</Text>
            <Text style={styles.statLabel}>Badges</Text>
          </View>
        </View>
        {settings.badges.length > 0 ? (
          <View style={[styles.toggle, { marginTop: space.md }]}>
            {settings.badges.map((b) => (
              <Chip key={b} label={`🏆 ${b}`} tone="good" active />
            ))}
          </View>
        ) : (
          <Text style={styles.hint}>Submit a label photo to earn your first badge!</Text>
        )}
      </Block>

      {/* Leaderboard */}
      <Block label="Leaderboard">
        <View style={styles.toggle}>
          <Chip
            label="National"
            tone={lbScope === "national" ? "warn" : "neutral"}
            active={lbScope === "national"}
            onPress={() => setLbScope("national")}
          />
          <Chip
            label={settings.city ? `${settings.city}` : "Local"}
            tone={lbScope === "local" ? "warn" : "neutral"}
            active={lbScope === "local"}
            onPress={() => setLbScope("local")}
          />
        </View>
        {lbLoading ? (
          <ActivityIndicator color={colors.accent} style={{ marginTop: space.md }} />
        ) : leaderboard.length > 0 ? (
          <View style={styles.lbList}>
            {leaderboard.map((entry, i) => (
              <View key={`${entry.display_name}-${i}`} style={styles.lbRow}>
                <Text style={styles.lbRank}>{i + 1}</Text>
                <Text style={styles.lbName} numberOfLines={1}>
                  {entry.display_name}
                </Text>
                <Text style={styles.lbPoints}>{entry.points} pts</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={[styles.hint, { marginTop: space.md }]}>No contributors yet. Be the first!</Text>
        )}
      </Block>

      <View style={styles.methodology}>
        <Text style={styles.methodTitle}>How we know</Text>
        <Text style={styles.methodBody}>
          No invented scores. Verified data comes from official checks. Community
          data is shown with a confidence label until two photos of the same
          label agree.
        </Text>
      </View>

      <Text style={styles.version}>TeaSpoon v5.0 · Know it in teaspoons, not grams.</Text>
    </ScrollView>
  );
}

function Block({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <View style={styles.block}>
      <Text style={styles.blockLabel}>{label}</Text>
      {children}
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  title: { color: colors.ink, fontSize: font.h1, fontWeight: weight.black, marginBottom: space.lg },
  block: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.lg,
    marginBottom: space.md,
    ...shadow.card,
  },
  blockLabel: { color: colors.ink, fontSize: font.title, fontWeight: weight.bold, marginBottom: space.md },
  toggle: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  hint: { color: colors.inkSoft, fontSize: font.small, marginTop: space.md, lineHeight: 18 },
  textInput: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: 10,
    fontSize: font.body,
    color: colors.ink,
    backgroundColor: colors.bg,
  },
  statsRow: { flexDirection: "row", gap: space.md },
  statBox: {
    flex: 1,
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    padding: space.md,
    alignItems: "center",
  },
  statNumber: { color: colors.accent, fontSize: font.h2, fontWeight: weight.black },
  statLabel: { color: colors.inkSoft, fontSize: font.small, marginTop: 2 },
  lbList: { marginTop: space.md },
  lbRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
  },
  lbRank: { color: colors.accent, fontSize: font.body, fontWeight: weight.bold, width: 28 },
  lbName: { color: colors.ink, fontSize: font.body, flex: 1 },
  lbPoints: { color: colors.inkSoft, fontSize: font.small, fontWeight: weight.semibold },
  methodology: { backgroundColor: colors.accentSoft, borderRadius: radius.lg, padding: space.md, marginTop: space.sm },
  methodTitle: { color: colors.accentDeep, fontSize: font.body, fontWeight: weight.bold, marginBottom: 6 },
  methodBody: { color: colors.inkSoft, fontSize: font.small, lineHeight: 19 },
  version: { color: colors.inkFaint, fontSize: font.tiny, textAlign: "center", marginTop: space.xl },
});
