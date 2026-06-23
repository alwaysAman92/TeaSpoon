import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Chip } from "@/components/Chip";
import { useApp } from "@/store/AppContext";
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
];

export function SettingsScreen() {
  const insets = useSafeAreaInsets();
  const { settings, saveSettings } = useApp();

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
        hint="Tightens your daily limits — diabetic caps sugar at 6 tsp, hypertensive caps sodium at 1500 mg."
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
  methodology: { backgroundColor: colors.accentSoft, borderRadius: radius.lg, padding: space.md, marginTop: space.sm },
  methodTitle: { color: colors.accentDeep, fontSize: font.body, fontWeight: weight.bold, marginBottom: 6 },
  methodBody: { color: colors.inkSoft, fontSize: font.small, lineHeight: 19 },
  version: { color: colors.inkFaint, fontSize: font.tiny, textAlign: "center", marginTop: space.xl },
});
