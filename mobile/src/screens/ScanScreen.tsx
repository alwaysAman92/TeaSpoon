import type { BottomTabScreenProps } from "@react-navigation/bottom-tabs";
import type { CompositeScreenProps } from "@react-navigation/native";
import { useIsFocused } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { CameraView, useCameraPermissions } from "expo-camera";
import React, { useCallback, useRef, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/api/client";
import { Chip } from "@/components/Chip";
import type { RootStackParamList, TabsParamList } from "@/navigation";
import { colors, font, radius, shadow, space, weight } from "@/theme";

type Props = CompositeScreenProps<
  BottomTabScreenProps<TabsParamList, "Scan">,
  NativeStackScreenProps<RootStackParamList>
>;

const isWeb = Platform.OS === "web";

// Quick-pick seeded products so the web preview (no camera) is easy to try.
const DEMOS = [
  { code: "8901058000108", label: "Maggi Noodles" },
  { code: "8901234500011", label: "Coca-Cola" },
  { code: "8901030712345", label: "Dairy Milk" },
  { code: "8901030966012", label: "Gummy Bears" },
  { code: "8901058822999", label: "Rolled Oats" },
];

export function ScanScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const isFocused = useIsFocused();
  const [permission, requestPermission] = useCameraPermissions();
  const [busy, setBusy] = useState(false);
  const [manualCode, setManualCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const lockRef = useRef(false);

  const handleBarcode = useCallback(
    async (code: string) => {
      if (lockRef.current) return;
      lockRef.current = true;
      setBusy(true);
      setError(null);
      try {
        const result = await api.scan(code, { log: true });
        navigation.navigate("Result", { result });
      } catch {
        setError("Couldn't reach the server. Is the API running on :8000?");
      } finally {
        setBusy(false);
        setTimeout(() => {
          lockRef.current = false;
        }, 1200);
      }
    },
    [navigation],
  );

  const submitManual = useCallback(async () => {
    const code = manualCode.trim();
    if (code.length < 6) {
      setError("Enter a valid barcode (6+ digits).");
      return;
    }
    setManualCode("");
    await handleBarcode(code);
  }, [manualCode, handleBarcode]);

  const ManualPanel = (
    <View style={styles.panel}>
      <Text style={styles.panelTitle}>Type a barcode</Text>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={manualCode}
          onChangeText={setManualCode}
          keyboardType="number-pad"
          placeholder="8901234567890"
          placeholderTextColor={colors.inkFaint}
          maxLength={14}
          onSubmitEditing={submitManual}
        />
        <Pressable style={styles.goBtn} onPress={submitManual} disabled={busy}>
          {busy ? <ActivityIndicator color={colors.white} /> : <Text style={styles.goText}>Go</Text>}
        </Pressable>
      </View>
      <Text style={styles.tryLabel}>Or try one of these:</Text>
      <View style={styles.demoRow}>
        {DEMOS.map((d) => (
          <Chip key={d.code} label={d.label} onPress={() => handleBarcode(d.code)} />
        ))}
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );

  // --- Web: never access the webcam. Manual entry + quick picks only. ------
  if (isWeb) {
    return (
      <ScrollView
        style={styles.lightScreen}
        contentContainerStyle={{ paddingTop: insets.top + space.xl, paddingHorizontal: space.lg, paddingBottom: 140 }}
      >
        <Text style={styles.bigLine}>Point. Scan. Know.</Text>
        <Text style={styles.subLine}>
          On a phone, TeaSpoon reads the barcode with your camera. In this web
          preview, enter a barcode or tap a sample below.
        </Text>
        {ManualPanel}
      </ScrollView>
    );
  }

  // --- Native: ask for permission, then show the camera (only when focused) -
  if (!permission) {
    return (
      <View style={[styles.darkScreen, styles.center]}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <ScrollView
        style={styles.lightScreen}
        contentContainerStyle={{ paddingTop: insets.top + space.xl, paddingHorizontal: space.lg, flexGrow: 1 }}
      >
        <Text style={styles.bigLine}>Point. Scan. Know.</Text>
        <Text style={styles.subLine}>
          TeaSpoon needs the camera to read barcodes. Nothing is recorded — we
          only read the code.
        </Text>
        <Pressable style={styles.primaryBtn} onPress={requestPermission}>
          <Text style={styles.primaryBtnText}>Allow camera</Text>
        </Pressable>
        {ManualPanel}
      </ScrollView>
    );
  }

  return (
    <View style={styles.darkScreen}>
      {/* Only mount the camera while this tab is focused, so it never holds
          the camera in the background. */}
      {isFocused ? (
        <CameraView
          style={StyleSheet.absoluteFill}
          facing="back"
          barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "upc_a", "upc_e"] }}
          onBarcodeScanned={busy ? undefined : ({ data }) => handleBarcode(data)}
        />
      ) : null}

      <View style={styles.overlay} pointerEvents="none">
        <View style={styles.frame} />
      </View>

      <View style={[styles.bottom, { paddingBottom: insets.bottom + space.xl }]}>
        {busy ? (
          <ActivityIndicator color={colors.onDark} />
        ) : (
          <Text style={styles.instruction}>Point at any barcode</Text>
        )}
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Pressable onPress={submitManual} hitSlop={12}>
          <Text style={styles.manualLink}>Enter barcode manually</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  lightScreen: { flex: 1, backgroundColor: colors.bg },
  darkScreen: { flex: 1, backgroundColor: colors.dark },
  center: { justifyContent: "center", alignItems: "center" },
  bigLine: { color: colors.ink, fontSize: font.h1, fontWeight: weight.black, marginBottom: space.sm },
  subLine: { color: colors.inkSoft, fontSize: font.body, lineHeight: 21, marginBottom: space.lg },
  panel: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.lg,
    marginTop: space.sm,
    ...shadow.card,
  },
  panelTitle: { color: colors.ink, fontSize: font.title, fontWeight: weight.bold, marginBottom: space.md },
  inputRow: { flexDirection: "row", gap: space.sm },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: 12,
    fontSize: font.title,
    color: colors.ink,
    backgroundColor: colors.surfaceAlt,
  },
  goBtn: {
    backgroundColor: colors.accent,
    borderRadius: radius.md,
    paddingHorizontal: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  goText: { color: colors.white, fontWeight: weight.bold, fontSize: font.body },
  tryLabel: { color: colors.inkSoft, fontSize: font.small, marginTop: space.lg, marginBottom: space.sm },
  demoRow: { flexDirection: "row", flexWrap: "wrap", gap: space.sm },
  primaryBtn: {
    backgroundColor: colors.accent,
    paddingVertical: 14,
    borderRadius: radius.pill,
    alignItems: "center",
    marginBottom: space.lg,
  },
  primaryBtnText: { color: colors.white, fontWeight: weight.bold, fontSize: font.body },
  overlay: { ...StyleSheet.absoluteFillObject, justifyContent: "center", alignItems: "center" },
  frame: { width: 250, height: 160, borderWidth: 3, borderColor: colors.accent, borderRadius: 16 },
  bottom: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    gap: space.md,
    paddingHorizontal: space.lg,
  },
  instruction: {
    color: colors.onDark,
    fontSize: font.h2,
    fontWeight: weight.bold,
    textShadowColor: "rgba(0,0,0,0.6)",
    textShadowRadius: 8,
  },
  manualLink: { color: colors.onDark, textDecorationLine: "underline", fontSize: font.body },
  error: { color: colors.danger, marginTop: space.sm },
});
