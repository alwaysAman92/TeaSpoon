import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, weight } from "@/theme";

type Tone = "neutral" | "star" | "nova" | "warn" | "good";

const TONES: Record<Tone, { bg: string; fg: string }> = {
  neutral: { bg: colors.surfaceSunken, fg: colors.inkSoft },
  star: { bg: "#FBEFD8", fg: "#C98A1E" },
  nova: { bg: colors.accentSoft, fg: colors.accentDeep },
  warn: { bg: colors.accent, fg: colors.white },
  good: { bg: colors.greenSoft, fg: colors.green },
};

interface Props {
  label: string;
  tone?: Tone;
  onPress?: () => void;
  active?: boolean;
}

export function Chip({ label, tone = "neutral", onPress, active }: Props) {
  const t = TONES[tone];
  
  if (!onPress) {
    return (
      <View style={[styles.chip, { backgroundColor: t.bg }, active && styles.active]}>
        <Text style={[styles.text, { color: t.fg }]}>{label}</Text>
      </View>
    );
  }

  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, { backgroundColor: t.bg }, active && styles.active]}
    >
      <Text style={[styles.text, { color: t.fg }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: radius.pill,
    alignSelf: "flex-start",
  },
  active: { borderWidth: 2, borderColor: colors.ink },
  text: { fontSize: 12.5, fontWeight: weight.semibold },
});
