import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { Stars } from "@/components/Stars";
import { colors, radius, shadow, space, weight } from "@/theme";
import type { Alternative } from "@/types";

export function AltCard({ alt }: { alt: Alternative }) {
  return (
    <View style={styles.card}>
      <Text style={styles.name} numberOfLines={2}>
        {alt.name}
      </Text>
      {alt.brand ? <Text style={styles.brand}>{alt.brand}</Text> : null}
      <View style={styles.reasonPill}>
        <Text style={styles.reason} numberOfLines={2}>
          {alt.reason}
        </Text>
      </View>
      <View style={styles.footer}>
        <Stars value={alt.hsr_stars} size={13} />
        {alt.price_inr != null ? (
          <Text style={styles.price}>₹{Math.round(alt.price_inr)}</Text>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: 176,
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.lg,
    padding: space.md,
    marginRight: space.sm,
    justifyContent: "space-between",
    minHeight: 158,
    ...shadow.card,
  },
  name: { color: colors.ink, fontSize: 15, fontWeight: weight.bold },
  brand: { color: colors.inkFaint, fontSize: 12, marginTop: 2 },
  reasonPill: {
    backgroundColor: colors.greenSoft,
    borderRadius: radius.sm,
    paddingVertical: 6,
    paddingHorizontal: 10,
    marginTop: 12,
  },
  reason: { color: colors.green, fontSize: 12.5, fontWeight: weight.semibold },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
  },
  price: { color: colors.ink, fontWeight: weight.bold, fontSize: 14 },
});
