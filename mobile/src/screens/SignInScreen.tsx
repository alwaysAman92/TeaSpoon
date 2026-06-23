import { useSignIn, useSignUp } from "@clerk/clerk-expo";
import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { colors, font, radius, shadow, space, weight } from "@/theme";

export function SignInScreen() {
  const insets = useSafeAreaInsets();
  const { signIn, isLoaded: isSignInLoaded, setActive: setSignInActive } = useSignIn();
  const { signUp, isLoaded: isSignUpLoaded, setActive: setSignUpActive } = useSignUp();

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [error, setError] = useState<string | null>(null);

  const handleContinue = async () => {
    if (!email.trim() || !email.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      if (!isSignInLoaded || !isSignUpLoaded) {
        throw new Error("Clerk authentication is not fully loaded. Please wait.");
      }

      // 1. Try to start the Sign In process
      try {
        await signIn.create({ identifier: email.trim().toLowerCase() });
        await signIn.prepareFirstFactor({ strategy: "email_code" });
        setVerifying(true);
        setMode("signin");
      } catch (err: any) {
        // 2. If user doesn't exist, start Sign Up instead
        const code = err.errors?.[0]?.code;
        if (code === "form_identifier_not_found" || code === "user_not_found") {
          await signUp.create({ emailAddress: email.trim().toLowerCase() });
          await signUp.prepareEmailAddressVerification({ strategy: "email_code" });
          setVerifying(true);
          setMode("signup");
        } else {
          throw err;
        }
      }
    } catch (err: any) {
      console.error("Clerk init auth error:", err);
      setError(err.errors?.[0]?.message || err.message || "Failed to send verification code.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (code.trim().length < 6) {
      setError("Please enter the 6-digit verification code.");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      if (mode === "signin") {
        if (!isSignInLoaded) return;
        const res = await signIn.attemptFirstFactor({
          strategy: "email_code",
          code: code.trim(),
        });
        if (res.status === "complete") {
          await setSignInActive({ session: res.createdSessionId });
        } else {
          setError(`Sign in status: ${res.status}. Please check details.`);
        }
      } else {
        if (!isSignUpLoaded) return;
        const res = await signUp.attemptEmailAddressVerification({
          code: code.trim(),
        });
        if (res.status === "complete") {
          await setSignUpActive({ session: res.createdSessionId });
        } else {
          setError(`Sign up status: ${res.status}. Please check details.`);
        }
      }
    } catch (err: any) {
      console.error("Clerk verify code error:", err);
      setError(err.errors?.[0]?.message || err.message || "Invalid verification code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <View style={[styles.inner, { paddingTop: insets.top + space.xxl, paddingBottom: insets.bottom + space.lg }]}>
        <View style={styles.header}>
          <Text style={styles.logo}>🥄 TeaSpoon</Text>
          <Text style={styles.subtitle}>Know it in teaspoons, not grams.</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>
            {verifying ? "Verify your email" : "Sign in or register"}
          </Text>
          <Text style={styles.cardDesc}>
            {verifying
              ? `We sent a 6-digit code to ${email}`
              : "Enter your email address to log in or create a new TeaSpoon account."}
          </Text>

          {error && <Text style={styles.errorText}>{error}</Text>}

          {!verifying ? (
            <View>
              <TextInput
                style={styles.textInput}
                value={email}
                onChangeText={(txt) => {
                  setEmail(txt);
                  setError(null);
                }}
                placeholder="you@example.com"
                placeholderTextColor={colors.inkFaint}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                editable={!loading}
              />
              <Pressable
                style={({ pressed }) => [styles.button, pressed && styles.buttonPressed, loading && styles.buttonDisabled]}
                onPress={handleContinue}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color={colors.white} />
                ) : (
                  <Text style={styles.buttonText}>Continue</Text>
                )}
              </Pressable>
            </View>
          ) : (
            <View>
              <TextInput
                style={[styles.textInput, styles.codeInput]}
                value={code}
                onChangeText={(txt) => {
                  setCode(txt);
                  setError(null);
                }}
                placeholder="123456"
                placeholderTextColor={colors.inkFaint}
                keyboardType="number-pad"
                maxLength={6}
                autoFocus
                editable={!loading}
              />
              <Pressable
                style={({ pressed }) => [styles.button, pressed && styles.buttonPressed, loading && styles.buttonDisabled]}
                onPress={handleVerify}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color={colors.white} />
                ) : (
                  <Text style={styles.buttonText}>Verify Code</Text>
                )}
              </Pressable>
              <Pressable
                style={styles.backButton}
                onPress={() => {
                  setVerifying(false);
                  setCode("");
                  setError(null);
                }}
                disabled={loading}
              >
                <Text style={styles.backButtonText}>← Use a different email</Text>
              </Pressable>
            </View>
          )}
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  inner: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: space.lg,
  },
  header: {
    alignItems: "center",
    marginBottom: space.xxl,
  },
  logo: {
    fontSize: font.h1 + 4,
    fontWeight: weight.black,
    color: colors.ink,
    letterSpacing: -1,
  },
  subtitle: {
    fontSize: font.body,
    fontWeight: weight.medium,
    color: colors.inkSoft,
    marginTop: space.xs,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.lg,
    ...shadow.card,
  },
  cardTitle: {
    fontSize: font.h2,
    fontWeight: weight.bold,
    color: colors.ink,
    marginBottom: space.xs,
  },
  cardDesc: {
    fontSize: font.small,
    color: colors.inkSoft,
    lineHeight: 18,
    marginBottom: space.lg,
  },
  errorText: {
    color: colors.danger,
    fontSize: font.small,
    fontWeight: weight.semibold,
    marginBottom: space.md,
  },
  textInput: {
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: 12,
    fontSize: font.body,
    color: colors.ink,
    marginBottom: space.md,
  },
  codeInput: {
    textAlign: "center",
    fontSize: font.h2,
    letterSpacing: 8,
    fontWeight: weight.bold,
  },
  button: {
    backgroundColor: colors.accent,
    borderRadius: radius.md,
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
    ...shadow.floating,
    elevation: 2,
  },
  buttonPressed: {
    backgroundColor: colors.accentDeep,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: colors.white,
    fontSize: font.body,
    fontWeight: weight.bold,
  },
  backButton: {
    alignItems: "center",
    marginTop: space.lg,
    paddingVertical: space.xs,
  },
  backButtonText: {
    color: colors.inkSoft,
    fontSize: font.small,
    fontWeight: weight.semibold,
  },
});
