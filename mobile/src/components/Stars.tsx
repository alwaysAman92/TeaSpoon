import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors } from "@/theme";

export function Stars({ value, size = 16 }: { value: number; size?: number }) {
  const full = Math.floor(value);
  const half = value - full >= 0.5;
  const stars: string[] = [];
  for (let i = 0; i < 5; i += 1) {
    if (i < full) stars.push("★");
    else if (i === full && half) stars.push("⯨");
    else stars.push("☆");
  }
  return (
    <View style={styles.row} accessibilityLabel={`${value} out of 5 stars`}>
      <Text style={[styles.stars, { fontSize: size }]}>{stars.join("")}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row" },
  stars: { color: colors.amber, letterSpacing: 1 },
});
