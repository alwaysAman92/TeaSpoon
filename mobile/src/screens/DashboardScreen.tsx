import type { BottomTabScreenProps } from "@react-navigation/bottom-tabs";
import { useFocusEffect } from "@react-navigation/native";
import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/api/client";
import { ProgressBar } from "@/components/ProgressBar";
import { ScanCard } from "@/components/ScanCard";
import { SemiGauge } from "@/components/SemiGauge";
import type { TabsParamList } from "@/navigation";
import { colors, font, radius, shadow, space, weight } from "@/theme";
import type { Dashboard } from "@/types";

type Props = BottomTabScreenProps<TabsParamList, "Dashboard">;

function isoOf(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const TODAY_ISO = isoOf(new Date());

// Last 7 calendar days, oldest -> newest (today on the right).
const DAY_STRIP = Array.from({ length: 7 }, (_, i) => {
  const d = new Date();
  d.setDate(d.getDate() - (6 - i));
  return {
    iso: isoOf(d),
    weekday: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][d.getDay()],
    day: d.getDate(),
    isToday: isoOf(d) === TODAY_ISO,
  };
});

export function DashboardScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(TODAY_ISO);
  const [showDateStrip, setShowDateStrip] = useState(false);
  const [showStreak, setShowStreak] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(false);

  const load = useCallback(async (date: string) => {
    try {
      setError(false);
      setDashboard(await api.dashboard(date === TODAY_ISO ? undefined : date));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load(selectedDate);
    }, [load, selectedDate]),
  );

  if (loading) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  const primary = dashboard?.primary;
  const isToday = selectedDate === TODAY_ISO;
  const streak = dashboard?.streak ?? 0;
  const headerDate = new Date(`${selectedDate}T00:00:00`);
  const headerTitle = isToday ? "Today" : headerDate.toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
  const gaugeDate = headerDate.toLocaleDateString([], { day: "numeric", month: "short" });

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: 130 }}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            void load(selectedDate);
          }}
          tintColor={colors.accent}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Pressable
          style={[styles.circleBtn, showDateStrip && styles.circleBtnActive]}
          onPress={() => {
            setShowStreak(false);
            setShowDateStrip((v) => !v);
          }}
          accessibilityLabel="Pick a day"
        >
          <Text style={[styles.circleGlyph, showDateStrip && styles.circleGlyphActive]}>📅</Text>
        </Pressable>

        <Text style={styles.headerTitle}>{headerTitle}</Text>

        <Pressable
          style={[styles.circleBtn, showStreak && styles.circleBtnActive]}
          onPress={() => {
            setShowDateStrip(false);
            setShowStreak((v) => !v);
          }}
          accessibilityLabel={`${streak} day streak`}
        >
          <Text style={styles.circleGlyph}>🔥</Text>
          {streak > 0 ? (
            <View style={styles.streakBadge}>
              <Text style={styles.streakBadgeText}>{streak}</Text>
            </View>
          ) : null}
        </Pressable>
      </View>

      {/* Day switcher (left button) */}
      {showDateStrip ? (
        <View style={styles.dateStrip}>
          {DAY_STRIP.map((d) => {
            const active = d.iso === selectedDate;
            return (
              <Pressable
                key={d.iso}
                style={[styles.dayPill, active && styles.dayPillActive]}
                onPress={() => {
                  setSelectedDate(d.iso);
                  setShowDateStrip(false);
                  setLoading(true);
                  void load(d.iso);
                }}
              >
                <Text style={[styles.dayWeekday, active && styles.dayTextActive]}>{d.weekday}</Text>
                <Text style={[styles.dayNum, active && styles.dayTextActive]}>{d.day}</Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}

      {/* Streak banner (right button) */}
      {showStreak ? (
        <View style={styles.streakBanner}>
          <Text style={styles.streakBannerText}>
            {streak > 0
              ? `🔥 ${streak}-day streak — log a scan each day to keep it alive.`
              : "No streak yet. Scan something today to start one."}
          </Text>
        </View>
      ) : null}

      {error && !dashboard ? (
        <Text style={styles.error}>Can't reach the server. Pull to retry.</Text>
      ) : null}

      {/* Hero gauge */}
      {primary ? (
        <View style={styles.gaugeWrap}>
          <SemiGauge
            value={primary.consumed}
            max={primary.target}
            fillColor={primary.is_goal ? colors.green : colors.accent}
            centerTop={gaugeDate}
            centerBig={`${formatNum(primary.consumed)} ${primary.unit}`}
            centerSub={`${primary.is_goal ? "Goal" : "Limit"} ${formatNum(primary.target)} ${primary.unit} ${primary.label.toLowerCase()}`}
          />
          <Text style={styles.takeaway}>{dashboard?.takeaway}</Text>
        </View>
      ) : null}

      {/* Body */}
      <View style={styles.body}>
        {isToday ? (
          <Pressable style={styles.addBtn} onPress={() => navigation.navigate("Scan")}>
            <Text style={styles.addGlyph}>＋</Text>
            <Text style={styles.addText}>Scan something</Text>
          </Pressable>
        ) : (
          <Pressable style={styles.backToday} onPress={() => setSelectedDate(TODAY_ISO)}>
            <Text style={styles.backTodayText}>← Back to today</Text>
          </Pressable>
        )}

        {/* Secondary nutrients */}
        <View style={styles.secondaryRow}>
          {dashboard?.secondary.slice(0, 3).map((s) => (
            <View key={s.key} style={styles.miniCard}>
              <Text style={styles.miniValue}>
                {formatNum(s.consumed)}
                <Text style={styles.miniUnit}>{s.unit === "%" ? "%" : s.unit}</Text>
              </Text>
              <Text style={styles.miniLabel}>{s.label}</Text>
              <View style={styles.miniBar}>
                <ProgressBar pct={s.pct} isGoal={s.is_goal} height={6} />
              </View>
            </View>
          ))}
        </View>

        {/* Recent scans */}
        <View style={styles.recentHead}>
          <Text style={styles.recentTitle}>{isToday ? "Today's scans" : "Scans"}</Text>
          <Text style={styles.recentCount}>{dashboard?.scans_today ?? 0}</Text>
        </View>

        {dashboard && dashboard.recent.length > 0 ? (
          dashboard.recent.map((scan, i) => <ScanCard key={`${scan.name}-${i}`} scan={scan} />)
        ) : (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>
              {isToday ? "Nothing logged yet. Scan a packet to start your day." : "Nothing logged on this day."}
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

function formatNum(n: number): string {
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 10) / 10);
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  center: { justifyContent: "center", alignItems: "center" },
  body: { paddingHorizontal: space.lg },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: space.lg,
    marginBottom: space.sm,
  },
  circleBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    ...shadow.card,
  },
  circleBtnActive: { backgroundColor: colors.accentSoft },
  circleGlyph: { fontSize: 18 },
  circleGlyphActive: {},
  streakBadge: {
    position: "absolute",
    top: -3,
    right: -3,
    minWidth: 18,
    height: 18,
    paddingHorizontal: 4,
    borderRadius: 9,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: colors.bg,
  },
  streakBadgeText: { color: colors.white, fontSize: 9, fontWeight: weight.black },
  headerTitle: { fontSize: font.title, fontWeight: weight.bold, color: colors.ink },
  dateStrip: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: space.lg,
    marginBottom: space.sm,
    gap: 6,
  },
  dayPill: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingVertical: 8,
    alignItems: "center",
    ...shadow.card,
  },
  dayPillActive: { backgroundColor: colors.accent },
  dayWeekday: { color: colors.inkFaint, fontSize: 10, fontWeight: weight.semibold },
  dayNum: { color: colors.ink, fontSize: font.body, fontWeight: weight.bold, marginTop: 2 },
  dayTextActive: { color: colors.white },
  streakBanner: {
    marginHorizontal: space.lg,
    marginBottom: space.sm,
    backgroundColor: colors.accentSoft,
    borderRadius: radius.md,
    padding: space.md,
  },
  streakBannerText: { color: colors.accentDeep, fontSize: font.small, fontWeight: weight.semibold },
  error: { color: colors.danger, textAlign: "center", marginTop: space.md },
  gaugeWrap: { alignItems: "center", marginTop: space.sm },
  takeaway: {
    color: colors.ink,
    fontSize: font.title,
    fontWeight: weight.bold,
    textAlign: "center",
    marginTop: space.md,
    paddingHorizontal: space.xl,
  },
  addBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: space.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.pill,
    paddingVertical: 14,
    marginTop: space.lg,
    ...shadow.card,
  },
  addGlyph: { color: colors.accent, fontSize: 20, fontWeight: weight.bold },
  addText: { color: colors.ink, fontSize: font.body, fontWeight: weight.semibold },
  backToday: {
    alignItems: "center",
    paddingVertical: 12,
    marginTop: space.lg,
  },
  backTodayText: { color: colors.accentDeep, fontSize: font.body, fontWeight: weight.semibold },
  secondaryRow: { flexDirection: "row", gap: space.sm, marginTop: space.lg },
  miniCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.md,
    ...shadow.card,
  },
  miniValue: { color: colors.ink, fontSize: font.h2, fontWeight: weight.bold },
  miniUnit: { color: colors.inkFaint, fontSize: font.small, fontWeight: weight.semibold },
  miniLabel: { color: colors.inkSoft, fontSize: font.small, marginTop: 2 },
  miniBar: { marginTop: space.sm },
  recentHead: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: space.xl,
    marginBottom: space.md,
  },
  recentTitle: { color: colors.ink, fontSize: font.title, fontWeight: weight.bold },
  recentCount: {
    color: colors.accent,
    fontSize: font.small,
    fontWeight: weight.bold,
    backgroundColor: colors.accentSoft,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: radius.pill,
    overflow: "hidden",
  },
  empty: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.lg,
    ...shadow.card,
  },
  emptyText: { color: colors.inkSoft, fontSize: font.body, textAlign: "center" },
});
