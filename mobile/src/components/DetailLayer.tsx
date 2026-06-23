import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Stars } from "@/components/Stars";
import { colors, font, radius, space, weight } from "@/theme";
import type { DetailLayer as Detail } from "@/types";

const VEG_META: Record<string, { color: string; bg: string; label: string }> = {
  veg: { color: colors.green, bg: colors.greenSoft, label: "Vegetarian" },
  non_veg: { color: colors.danger, bg: colors.dangerSoft, label: "Non-vegetarian" },
  uncertain: { color: colors.amber, bg: "#FBEFD8", label: "Veg status uncertain" },
};

export function DetailLayer({ detail }: { detail: Detail }) {
  const veg = VEG_META[detail.ingredients.veg_status] ?? VEG_META.uncertain;

  return (
    <View style={styles.wrap}>
      {/* F6 - Health Star Rating */}
      <Section title="Health Star Rating">
        <View style={styles.hsrRow}>
          <Stars value={detail.hsr.stars} size={22} />
          <Text style={styles.hsrValue}>{detail.hsr.stars.toFixed(1)} / 5</Text>
        </View>
        <Text style={styles.note}>
          FSANZ formula · baseline {detail.hsr.baseline_points} − modifying{" "}
          {detail.hsr.modifying_points}
          {detail.hsr.protein_counted ? "" : " · protein didn't count (too unhealthy to offset)"}
        </Text>
      </Section>

      {/* F7 - NOVA */}
      <Section title="Processing level">
        <Text style={styles.novaTag}>{detail.nova.tag}</Text>
        <Text style={styles.note}>{detail.nova.rationale}</Text>
      </Section>

      {/* F8 - Claims */}
      {detail.claims.findings.length > 0 ? (
        <Section title="Marketing vs reality">
          {detail.claims.findings.map((f, i) => (
            <View key={`${f.claim}-${i}`} style={styles.claimRow}>
              <Text style={[styles.claimDot, { color: verdictColor(f.verdict) }]}>●</Text>
              <View style={styles.flex}>
                <Text style={styles.claimName}>
                  {f.claim} · <Text style={{ color: verdictColor(f.verdict) }}>{f.verdict}</Text>
                </Text>
                <Text style={styles.note}>{f.explanation}</Text>
              </View>
            </View>
          ))}
        </Section>
      ) : null}

      {/* F9 - Ingredients & veg/non-veg */}
      <Section title="Ingredients">
        <Text style={[styles.vegBadge, { color: veg.color, backgroundColor: veg.bg }]}>
          {veg.label}
        </Text>
        <Text style={styles.note}>{detail.ingredients.note}</Text>
        {detail.ingredients.non_veg_flags.map((f) => (
          <Text key={f.ingredient} style={styles.flag}>
            ⚠ {f.explanation}
          </Text>
        ))}
        {detail.ingredients.additives.length > 0 ? (
          <View style={styles.additives}>
            {detail.ingredients.additives.map((a) => (
              <Text key={a.code} style={styles.additive}>
                <Text style={styles.additiveCode}>{a.code}</Text> {a.plain_english}
              </Text>
            ))}
          </View>
        ) : null}
      </Section>
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function verdictColor(verdict: string): string {
  if (verdict === "misleading") return colors.danger;
  if (verdict === "honest") return colors.green;
  return colors.amber;
}

const styles = StyleSheet.create({
  wrap: { marginTop: space.md, gap: space.sm },
  section: { backgroundColor: colors.surfaceAlt, borderRadius: radius.lg, padding: space.md },
  sectionTitle: {
    color: colors.inkFaint,
    fontSize: font.tiny,
    fontWeight: weight.bold,
    textTransform: "uppercase",
    letterSpacing: 1.2,
    marginBottom: space.sm,
  },
  hsrRow: { flexDirection: "row", alignItems: "center", gap: space.sm },
  hsrValue: { color: colors.ink, fontSize: font.title, fontWeight: weight.bold },
  novaTag: { color: colors.accentDeep, fontSize: font.body, fontWeight: weight.bold },
  note: { color: colors.inkSoft, fontSize: font.small, marginTop: 4, lineHeight: 18 },
  claimRow: { flexDirection: "row", gap: space.sm, marginBottom: space.sm },
  claimDot: { fontSize: 10, marginTop: 4 },
  claimName: { color: colors.ink, fontSize: font.body, fontWeight: weight.semibold },
  flex: { flex: 1 },
  vegBadge: {
    alignSelf: "flex-start",
    borderRadius: radius.sm,
    paddingVertical: 4,
    paddingHorizontal: 10,
    fontSize: font.small,
    fontWeight: weight.bold,
    marginBottom: 6,
    overflow: "hidden",
  },
  flag: { color: colors.danger, fontSize: font.small, marginTop: 6 },
  additives: { marginTop: space.sm, gap: 4 },
  additive: { color: colors.inkSoft, fontSize: font.small, lineHeight: 18 },
  additiveCode: { color: colors.accentDeep, fontWeight: weight.bold },
});
