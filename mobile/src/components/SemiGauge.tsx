import React from "react";
import { StyleSheet, Text, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { colors, font, weight } from "@/theme";

interface Props {
  value: number;
  max: number;
  segments?: number;
  width?: number;
  strokeWidth?: number;
  fillColor?: string;
  centerTop?: string;
  centerBig?: string;
  centerSub?: string;
}

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const a = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) };
}

function arc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const s = polar(cx, cy, r, startAngle);
  const e = polar(cx, cy, r, endAngle);
  // sweep-flag 1 = clockwise on screen (SVG y-down)
  return `M ${s.x} ${s.y} A ${r} ${r} 0 0 1 ${e.x} ${e.y}`;
}

/** A segmented semicircular gauge (the reference dashboard's hero element). */
export function SemiGauge({
  value,
  max,
  segments = 10,
  width = 270,
  strokeWidth = 16,
  fillColor = colors.accent,
  centerTop,
  centerBig,
  centerSub,
}: Props) {
  const height = width / 2 + strokeWidth;
  const cx = width / 2;
  const cy = height - strokeWidth / 2;
  const r = width / 2 - strokeWidth / 2 - 2;

  const gapDeg = 3;
  const segDeg = (180 - gapDeg * (segments - 1)) / segments;
  const ratio = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0;
  const filled = Math.round(ratio * segments);

  const paths = Array.from({ length: segments }, (_, i) => {
    const start = 180 - i * (segDeg + gapDeg);
    const end = start - segDeg;
    return {
      d: arc(cx, cy, r, start, end),
      on: i < filled,
    };
  });

  return (
    <View style={{ width, height, alignItems: "center" }}>
      <Svg width={width} height={height}>
        {paths.map((p, i) => (
          <Path
            key={i}
            d={p.d}
            stroke={p.on ? fillColor : colors.accentTrack}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            fill="none"
          />
        ))}
      </Svg>
      <View style={[styles.center, { width, height }]} pointerEvents="none">
        {centerTop ? <Text style={styles.top}>{centerTop}</Text> : null}
        {centerBig ? <Text style={styles.big}>{centerBig}</Text> : null}
        {centerSub ? <Text style={[styles.sub, { color: fillColor }]}>{centerSub}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "flex-end",
    paddingBottom: 6,
  },
  top: { color: colors.inkSoft, fontSize: font.small, fontWeight: weight.semibold, marginBottom: 2 },
  big: { color: colors.ink, fontSize: font.big, fontWeight: weight.black, lineHeight: font.big },
  sub: { fontSize: font.body, fontWeight: weight.bold, marginTop: 2 },
});
