import React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { colors, font, radius, shadow, space, weight } from "@/theme";
import type { RecentScan } from "@/types";

const CATEGORY_EMOJI: Record<string, string> = {
  beverages: "🥤",
  dairy_beverages: "🥛",
  dairy_food: "🧈",
  fats_oils: "🫒",
  cheese: "🧀",
  general_food: "🍪",
};

export function ScanCard({ scan }: { scan: RecentScan }) {
  return (
    <View style={styles.card}>
      <View style={styles.thumb}>
        {scan.image_url ? (
          <Image source={{ uri: scan.image_url }} style={styles.thumbImg} />
        ) : (
          <Text style={styles.thumbEmoji}>{CATEGORY_EMOJI[scan.category] ?? "🍪"}</Text>
        )}
      </View>

      <View style={styles.middle}>
        <Text style={styles.name} numberOfLines={1}>
          {scan.name}
        </Text>
        <Text style={styles.time}>{formatTime(scan.logged_at)}</Text>
        <View style={styles.macros}>
          <Macro label="Sugar" value={`${round(scan.sugar_tsp)} tsp`} />
          <Macro label="Sodium" value={`${Math.round(scan.sodium_mg)}mg`} />
          <Macro label="Protein" value={`${round(scan.protein_g)}g`} />
        </View>
      </View>

      <View style={styles.right}>
        <Text style={styles.bigStat}>{round(scan.sugar_tsp)}</Text>
        <Text style={styles.bigUnit}>tsp sugar</Text>
      </View>
    </View>
  );
}

function Macro({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.macro}>
      <Text style={styles.macroValue}>{value}</Text>
      <Text style={styles.macroLabel}>{label}</Text>
    </View>
  );
}

function round(n: number): string {
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 10) / 10);
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.md,
    marginBottom: space.sm,
    ...shadow.card,
  },
  thumb: {
    width: 48,
    height: 48,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceSunken,
    alignItems: "center",
    justifyContent: "center",
    marginRight: space.md,
  },
  thumbImg: { width: 48, height: 48, borderRadius: radius.md },
  thumbEmoji: { fontSize: 24 },
  middle: { flex: 1 },
  name: { color: colors.ink, fontSize: font.body, fontWeight: weight.bold },
  time: { color: colors.inkFaint, fontSize: font.tiny, marginTop: 1 },
  macros: { flexDirection: "row", gap: space.md, marginTop: 8 },
  macro: {},
  macroValue: { color: colors.ink, fontSize: font.small, fontWeight: weight.semibold },
  macroLabel: { color: colors.inkFaint, fontSize: 10 },
  right: { alignItems: "flex-end", marginLeft: space.sm },
  bigStat: { color: colors.accent, fontSize: font.h1, fontWeight: weight.black, lineHeight: font.h1 },
  bigUnit: { color: colors.inkFaint, fontSize: font.tiny },
});
