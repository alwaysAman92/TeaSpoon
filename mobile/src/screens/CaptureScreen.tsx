import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { CameraView, useCameraPermissions } from "expo-camera";
import React, { useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { api } from "@/api/client";
import type { RootStackParamList } from "@/navigation";
import { colors, font, radius, shadow, space, weight } from "@/theme";

type Props = NativeStackScreenProps<RootStackParamList, "Capture">;

export function CaptureScreen({ route, navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { barcode } = route.params;
  const [permission, requestPermission] = useCameraPermissions();
  const [uploading, setUploading] = useState(false);
  const [done, setDone] = useState(false);
  const cameraRef = useRef<CameraView>(null);

  const capture = async () => {
    if (!cameraRef.current || uploading) return;
    setUploading(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.7 });
      if (!photo?.uri) throw new Error("No photo captured");
      await api.submitContribution(barcode, photo.uri);
      setDone(true);
      setTimeout(() => navigation.goBack(), 1800);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      Alert.alert("Oops", msg);
    } finally {
      setUploading(false);
    }
  };

  if (!permission) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={[styles.screen, styles.center, { paddingHorizontal: space.xl }]}>
        <Text style={styles.heading}>Camera needed</Text>
        <Text style={styles.body}>
          We need the camera to photograph the nutrition label. Nothing is recorded beyond the label.
        </Text>
        <Pressable style={styles.primaryBtn} onPress={requestPermission}>
          <Text style={styles.primaryBtnText}>Allow camera</Text>
        </Pressable>
        <Pressable onPress={() => navigation.goBack()}>
          <Text style={styles.backLink}>← Go back</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />

      {/* Overlay */}
      <View style={styles.overlay} pointerEvents="none">
        <View style={styles.frame} />
        <Text style={styles.instruction}>
          Snap the nutrition label table clearly
        </Text>
      </View>

      {/* Bottom controls */}
      <View style={[styles.bottom, { paddingBottom: insets.bottom + space.xl }]}>
        {done ? (
          <View style={styles.doneWrap}>
            <Text style={styles.doneText}>✓ Submitted! Thanks for helping.</Text>
          </View>
        ) : (
          <>
            <Pressable style={styles.captureBtn} onPress={capture} disabled={uploading}>
              {uploading ? (
                <ActivityIndicator color={colors.white} />
              ) : (
                <View style={styles.captureInner} />
              )}
            </Pressable>
            <Text style={styles.barcodeLabel}>Barcode: {barcode}</Text>
          </>
        )}

        <Pressable onPress={() => navigation.goBack()} hitSlop={12}>
          <Text style={styles.cancelLink}>Cancel</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.dark },
  center: { justifyContent: "center", alignItems: "center" },
  heading: { color: colors.ink, fontSize: font.h2, fontWeight: weight.black, textAlign: "center", marginBottom: space.md },
  body: { color: colors.inkSoft, fontSize: font.body, textAlign: "center", marginBottom: space.xl, lineHeight: 21 },
  primaryBtn: {
    backgroundColor: colors.accent,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: radius.pill,
    marginBottom: space.md,
  },
  primaryBtnText: { color: colors.white, fontWeight: weight.bold, fontSize: font.body },
  backLink: { color: colors.inkSoft, fontSize: font.body, textDecorationLine: "underline" },
  overlay: { ...StyleSheet.absoluteFillObject, justifyContent: "center", alignItems: "center" },
  frame: { width: 280, height: 200, borderWidth: 3, borderColor: colors.accent, borderRadius: 16 },
  instruction: {
    color: colors.onDark,
    fontSize: font.body,
    fontWeight: weight.semibold,
    marginTop: space.lg,
    textShadowColor: "rgba(0,0,0,0.7)",
    textShadowRadius: 8,
    textAlign: "center",
    paddingHorizontal: space.xl,
  },
  bottom: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    gap: space.md,
    paddingHorizontal: space.lg,
  },
  captureBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "rgba(255,255,255,0.3)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 4,
    borderColor: colors.white,
  },
  captureInner: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: colors.white,
  },
  barcodeLabel: {
    color: colors.onDark,
    fontSize: font.small,
    fontWeight: weight.semibold,
    backgroundColor: "rgba(0,0,0,0.5)",
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: radius.pill,
    overflow: "hidden",
  },
  doneWrap: {
    backgroundColor: colors.green,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: radius.pill,
  },
  doneText: { color: colors.white, fontWeight: weight.bold, fontSize: font.body },
  cancelLink: { color: colors.onDark, fontSize: font.body, textDecorationLine: "underline" },
});
