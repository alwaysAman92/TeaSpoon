import React from "react";
import { StyleSheet, View } from "react-native";

import { colors, radius } from "@/theme";

interface Props {
  pct: number;
  // Goal bars (protein/fibre) are green; ceiling bars go amber -> red as they fill.
  isGoal?: boolean;
  height?: number;
  track?: string;
}

export function ProgressBar({ pct, isGoal = false, height = 12, track = colors.accentTrack }: Props) {
  const clamped = Math.max(0, Math.min(100, pct));
  let fill = colors.accent;
  if (isGoal) {
    fill = colors.green;
  } else if (pct >= 100) {
    fill = colors.danger;
  } else if (pct >= 80) {
    fill = colors.amber;
  }

  return (
    <View style={[styles.track, { height, backgroundColor: track }]}>
      <View style={[styles.fill, { width: `${clamped}%`, backgroundColor: fill, height }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: { borderRadius: radius.pill, overflow: "hidden", width: "100%" },
  fill: { borderRadius: radius.pill },
});
