import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/api/client";
import { AltCard } from "@/components/AltCard";
import { Chip } from "@/components/Chip";
import { DetailLayer } from "@/components/DetailLayer";
import type { RootStackParamList } from "@/navigation";
import { useApp } from "@/store/AppContext";
import { colors, font, radius, shadow, space, weight } from "@/theme";

type Props = NativeStackScreenProps<RootStackParamList, "Result">;

const TRUST_LABEL: Record<string, string> = {
  verified: "Verified",
  confirmed: "Confirmed",
  pending: "Unconfirmed",
};

export function ResultScreen({ route, navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { result } = route.params;
  const [showDetail, setShowDetail] = useState(false);
  const [reported, setReported] = useState(false);
  const [viewMode, setViewMode] = useState<"serving" | "pack">("serving");

  const headline = useMemo(() => {
    const key = result.headline_nutrient ?? "sugar";
    return result.translation.find((t) => t.key === key) ?? result.translation[0];
  }, [result]);

  if (!result.found || !result.product) {
    return (
      <View style={[styles.screen, styles.center, { padding: space.xl }]}>
        <Text style={styles.notFoundBig}>New to us.</Text>
        <Text style={styles.notFoundBody}>
          {result.message ?? "Snap the nutrition label and we'll read it for you."}
        </Text>
        <Pressable
          style={styles.cta}
          onPress={() => navigation.navigate("Capture", { barcode: route.params.result.product?.barcode ?? "unknown" })}
        >
          <Text style={styles.ctaText}>Snap the label</Text>
        </Pressable>
      </View>
    );
  }

  const product = result.product;
  const detail = result.detail;
  const trust = TRUST_LABEL[result.trust_tier ?? product.trust_tier] ?? "Unconfirmed";

  const hasPackSize = !!(
    product.package_weight_g &&
    product.serving_size_g &&
    product.package_weight_g > product.serving_size_g
  );

  const multiplier = useMemo(() => {
    if (viewMode === "pack" && hasPackSize) {
      return product.package_weight_g! / product.serving_size_g;
    }
    return 1;
  }, [viewMode, hasPackSize, product.package_weight_g, product.serving_size_g]);

  const heroParts = (headline?.headline ?? "").split(" ");
  const heroNumberRaw = heroParts[0] ?? "";
  const heroRest = heroParts.slice(1).join(" ");

  const scaledHeroNumber = useMemo(() => {
    const parsed = parseFloat(heroNumberRaw);
    if (isNaN(parsed)) {
      return heroNumberRaw;
    }
    return formatNum(parsed * multiplier);
  }, [heroNumberRaw, multiplier]);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={{ paddingTop: insets.top + space.md, paddingBottom: 60 }}
    >
      <View style={styles.body}>
        <View style={styles.topRow}>
          <Pressable onPress={() => navigation.goBack()} hitSlop={12} style={styles.closeBtn}>
            <Text style={styles.close}>✕</Text>
          </Pressable>
          <Text style={[styles.trust, trust === "Verified" && styles.trustVerified]}>{trust}</Text>
        </View>

        <Text style={styles.product}>{product.name}</Text>
        {product.brand ? <Text style={styles.brand}>{product.brand}</Text> : null}

        {/* Serving size toggle */}
        {hasPackSize && (
          <View style={styles.toggleOuter}>
            <Pressable
              style={[styles.toggleBtn, viewMode === "serving" && styles.toggleBtnActive]}
              onPress={() => setViewMode("serving")}
            >
              <Text style={[styles.toggleText, viewMode === "serving" && styles.toggleTextActive]}>
                Per Serving ({product.serving_size_g}g)
              </Text>
            </Pressable>
            <Pressable
              style={[styles.toggleBtn, viewMode === "pack" && styles.toggleBtnActive]}
              onPress={() => setViewMode("pack")}
            >
              <Text style={[styles.toggleText, viewMode === "pack" && styles.toggleTextActive]}>
                Whole Pack ({product.package_weight_g}g)
              </Text>
            </Pressable>
          </View>
        )}

        {/* Hero stat — oversized, the first thing the eye hits. */}
        <View style={styles.heroCard}>
          <Text style={styles.heroBig}>{scaledHeroNumber}</Text>
          <Text style={styles.heroRest}>{heroRest}</Text>
          <Text style={styles.servingLabel}>
            {viewMode === "pack"
              ? `for the whole pack of ${product.package_weight_g}g`
              : `per serving of ${product.serving_size_g}g`}
          </Text>
        </View>

        {/* Allergen warning — high visibility if user has allergy profile */}
        <AllergenWarning allergens={detail?.ingredients?.allergens_detected} />

        {/* Other translated nutrients. */}
        <View style={styles.translationRow}>
          {result.translation
            .filter((t) => t.key !== headline?.key)
            .map((t) => (
              <View key={t.key} style={styles.tItem}>
                <Text style={styles.tValue}>
                  {formatNum(t.plain_value * multiplier)}
                  <Text style={styles.tUnit}> {t.plain_unit === "% daily limit" ? "%" : t.plain_unit}</Text>
                </Text>
                <Text style={styles.tLabel}>{t.label}</Text>
              </View>
            ))}
        </View>

        {/* F5 — Alternatives on EVERY scan, always present. */}
        <Text style={styles.swipeLabel}>
          {result.alternatives.length > 0 ? "Better picks →" : "Best in its aisle"}
        </Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingRight: space.lg }}>
          {result.alternatives.length > 0 ? (
            result.alternatives.map((alt) => <AltCard key={alt.id} alt={alt} />)
          ) : (
            <View style={styles.noAlt}>
              <Text style={styles.noAltText}>This is already a strong choice here.</Text>
            </View>
          )}
        </ScrollView>

        {/* Secondary chips — tap to expand the detail layer (collapsed by default). */}
        {detail ? (
          <Pressable onPress={() => setShowDetail((v) => !v)}>
            <View style={styles.chipRow}>
              <Chip label={`★ ${detail.hsr.stars.toFixed(1)}`} tone="star" />
              <Chip label={`NOVA ${detail.nova.group}`} tone="nova" />
              {detail.claims.badge ? <Chip label={detail.claims.badge} tone="warn" /> : null}
              <Chip label={showDetail ? "Hide details ▲" : "Tap for details ▼"} />
            </View>
          </Pressable>
        ) : null}

        {showDetail && detail ? <DetailLayer detail={detail} /> : null}

        {/* Today's running total updated by this scan. */}
        {result.dashboard ? (
          <View style={styles.dashCard}>
            <Text style={styles.dashTakeaway}>{result.dashboard.takeaway}</Text>
            <Text style={styles.dashHeadline}>{result.dashboard.primary.headline}</Text>
          </View>
        ) : null}

        <Pressable
          disabled={reported}
          onPress={async () => {
            try {
              await api.reportData(product.barcode, "user flagged from result screen");
              setReported(true);
            } catch {
              /* best effort */
            }
          }}
        >
          <Text style={styles.report}>
            {reported ? "Thanks — we'll re-check it." : "Report incorrect data"}
          </Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

function formatNum(n: number): string {
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 10) / 10);
}

function AllergenWarning({ allergens }: { allergens?: string[] }) {
  const { settings } = useApp();
  const hasAllergyProfile = settings?.health_flags?.includes("allergy");
  if (!hasAllergyProfile || !allergens || allergens.length === 0) return null;
  return (
    <View style={styles.allergenCard}>
      <Text style={styles.allergenTitle}>⚠️ Allergen Warning</Text>
      <Text style={styles.allergenBody}>Contains: {allergens.join(", ")}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  center: { justifyContent: "center", alignItems: "center" },
  body: { paddingHorizontal: space.lg },
  topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  closeBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.surface,
    alignItems: "center",
    justifyContent: "center",
    ...shadow.card,
  },
  close: { color: colors.ink, fontSize: 18, fontWeight: weight.bold },
  trust: {
    color: colors.inkSoft,
    fontSize: font.tiny,
    fontWeight: weight.bold,
    textTransform: "uppercase",
    letterSpacing: 1,
    borderWidth: 1,
    borderColor: colors.inkFaint,
    borderRadius: radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 4,
    overflow: "hidden",
  },
  trustVerified: { color: colors.green, borderColor: colors.green },
  product: { color: colors.ink, fontSize: font.h2, fontWeight: weight.black, marginTop: space.lg },
  brand: { color: colors.inkSoft, fontSize: font.body, marginTop: 2 },
  heroCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    paddingVertical: space.lg,
    paddingHorizontal: space.lg,
    marginTop: space.lg,
    marginBottom: space.md,
    ...shadow.card,
  },
  heroBig: { color: colors.accent, fontSize: font.hero, fontWeight: weight.black, lineHeight: font.hero },
  heroRest: { color: colors.ink, fontSize: font.h2, fontWeight: weight.bold, marginTop: 2 },
  servingLabel: { color: colors.inkSoft, fontSize: font.small, fontWeight: weight.semibold, marginTop: space.sm },
  toggleOuter: {
    flexDirection: "row",
    backgroundColor: colors.surfaceSunken,
    borderRadius: radius.pill,
    padding: 4,
    marginTop: space.md,
    borderWidth: 1,
    borderColor: colors.line,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: radius.pill,
  },
  toggleBtnActive: {
    backgroundColor: colors.surface,
    ...shadow.card,
  },
  toggleText: {
    fontSize: font.small,
    fontWeight: weight.bold,
    color: colors.inkSoft,
  },
  toggleTextActive: {
    color: colors.accent,
  },
  translationRow: { flexDirection: "row", flexWrap: "wrap", gap: space.xl, marginBottom: space.xl },
  tItem: {},
  tValue: { color: colors.ink, fontSize: font.title, fontWeight: weight.bold },
  tUnit: { color: colors.inkSoft, fontSize: font.small, fontWeight: weight.semibold },
  tLabel: { color: colors.inkFaint, fontSize: font.tiny, marginTop: 2 },
  swipeLabel: { color: colors.inkSoft, fontSize: font.small, fontWeight: weight.semibold, marginBottom: space.sm },
  noAlt: { backgroundColor: colors.surface, borderRadius: radius.lg, padding: space.md, width: 240, ...shadow.card },
  noAltText: { color: colors.green, fontSize: font.body, fontWeight: weight.semibold },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: space.sm, marginTop: space.lg },
  dashCard: { backgroundColor: colors.accentSoft, borderRadius: radius.lg, padding: space.md, marginTop: space.lg },
  dashTakeaway: { color: colors.accentDeep, fontSize: font.title, fontWeight: weight.bold },
  dashHeadline: { color: colors.inkSoft, fontSize: font.small, marginTop: 4 },
  report: { color: colors.inkFaint, fontSize: font.small, textDecorationLine: "underline", marginTop: space.xl, textAlign: "center" },
  notFoundBig: { color: colors.ink, fontSize: font.h1, fontWeight: weight.black, textAlign: "center" },
  notFoundBody: { color: colors.inkSoft, fontSize: font.body, textAlign: "center", marginTop: space.md, marginBottom: space.xl },
  cta: { backgroundColor: colors.accent, paddingVertical: 14, paddingHorizontal: 28, borderRadius: radius.pill },
  ctaText: { color: colors.white, fontWeight: weight.bold, fontSize: font.body },
  allergenCard: {
    backgroundColor: "#FFF3CD",
    borderRadius: radius.lg,
    padding: space.md,
    marginBottom: space.md,
    borderWidth: 1,
    borderColor: "#FFCA2C",
  },
  allergenTitle: { color: "#856404", fontSize: font.title, fontWeight: weight.bold, marginBottom: 4 },
  allergenBody: { color: "#856404", fontSize: font.body, lineHeight: 20 },
});
