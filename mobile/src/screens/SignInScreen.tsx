import { useSignIn, useSignUp } from "@clerk/clerk-expo";
import React, { useState, useRef } from "react";
import {
  ActivityIndicator,
  Animated,
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Path, G } from "react-native-svg";

import { useApp } from "@/store/AppContext";
import { colors, font, radius, shadow, space, weight } from "@/theme";

function GoogleIcon({ size = 22 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <G fill="none" fillRule="evenodd">
        <Path
          fill="#4285F4"
          d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v3.92h6.69c-.29 1.5-.14 3.08-3.08 4.05v2.54h4.99c2.92-2.69 4.14-6.65 4.14-10.44z"
        />
        <Path
          fill="#34A853"
          d="M12 24c3.24 0 5.97-1.08 7.96-2.91l-4.99-2.54c-1.39.93-3.17 1.48-4.97 1.48-4.83 0-8.91-3.26-10.37-7.64H2.43v2.62C4.43 20.35 7.94 24 12 24z"
        />
        <Path
          fill="#FBBC05"
          d="M1.63 12.39a14.28 14.28 0 0 1 0-4.78V4.99H2.43c-1.46 4.38-1.46 9.02 0 13.4l2.14-1.63L1.63 12.39z"
        />
        <Path
          fill="#EA4335"
          d="M12 4.75c1.77-.03 3.47.64 4.73 1.85l3.52-3.52C18.03 1.04 15.13.02 12 0 7.94 0 4.43 3.65 2.43 7.61L4.57 9.24C6.03 4.86 10.11 4.75 12 4.75z"
        />
      </G>
    </Svg>
  );
}

function AppleIcon({ size = 20 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="#000000">
      <Path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.17c.65-.79 1.09-1.9 1-3.01-1 .04-2.22.67-2.94 1.5-.64.74-1.2 1.87-1.04 2.97 1.12.09 2.27-.58 2.98-1.46Z" />
    </Svg>
  );
}

const ONBOARDING_SLIDES = [
  {
    key: "scan",
    title: "Know your food\nin teaspoons",
    subtitle: "Scan packet barcodes to instantly see sugar, sodium, and protein translated into simple teaspoons.",
  },
  {
    key: "budget",
    title: "Stay within your\ndaily budget",
    subtitle: "Watch your day add up automatically. Stay under your daily limits and hit your protein target.",
  },
  {
    key: "goals",
    title: "Tailored to your\nhealth profile",
    subtitle: "Choose health goals to automatically tighten daily limits for sugar and sodium.",
  },
];

const GOAL_OPTIONS = [
  { key: "diabetic", label: "Diabetic Focus", desc: "Caps daily sugar at 6 tsp", emoji: "🍬" },
  { key: "hypertensive", label: "Sodium Limit", desc: "Caps daily sodium at 1500mg", emoji: "🧂" },
  { key: "weight_goal", label: "Weight Goal", desc: "Prioritizes high-protein options", emoji: "🎯" },
  { key: "allergy", label: "Allergy Alert", desc: "Warns about allergen ingredients", emoji: "⚠️" },
];

export function SignInScreen() {
  const insets = useSafeAreaInsets();
  const { signIn, isLoaded: isSignInLoaded, setActive: setSignInActive } = useSignIn();
  const { signUp, isLoaded: isSignUpLoaded, setActive: setSignUpActive } = useSignUp();
  const { settings, saveSettings } = useApp();

  const [showGetStarted, setShowGetStarted] = useState(true);
  const [slideIndex, setSlideIndex] = useState(0);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [error, setError] = useState<string | null>(null);

  // Animations
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;

  const healthFlags = settings?.health_flags ?? [];

  const toggleHealthFlag = (flag: string) => {
    const active = healthFlags.includes(flag);
    const nextFlags = active
      ? healthFlags.filter((f) => f !== flag)
      : [...healthFlags, flag];
    void saveSettings({ health_flags: nextFlags });
  };

  const goToSlide = (nextIndex: number) => {
    if (nextIndex < 0 || nextIndex >= ONBOARDING_SLIDES.length) return;

    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 120,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: -30,
        duration: 120,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setSlideIndex(nextIndex);
      slideAnim.setValue(30);
      Animated.parallel([
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 180,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: 180,
          useNativeDriver: true,
        }),
      ]).start();
    });
  };

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

      try {
        const signInAttempt = await signIn.create({ identifier: email.trim().toLowerCase() });
        const emailFactor = signInAttempt.supportedFirstFactors?.find(
          (f: any) => f.strategy === "email_code"
        );
        if (!emailFactor || !("emailAddressId" in emailFactor)) {
          throw new Error("Email verification is not supported for this account.");
        }
        await signIn.prepareFirstFactor({
          strategy: "email_code",
          emailAddressId: (emailFactor as any).emailAddressId,
        });
        setVerifying(true);
        setMode("signin");
      } catch (err: any) {
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
      setError(err.errors?.[0]?.longMessage || err.errors?.[0]?.message || err.message || "Failed to send verification code.");
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
        console.log("SIGN UP RESULT:", JSON.stringify(res, null, 2));
        if (res.status === "complete") {
          await setSignUpActive({ session: res.createdSessionId });
        } else {
          const missing = (res as any).missingFields ? ` Missing: ${(res as any).missingFields.join(", ")}` : "";
          setError(`Sign up status: ${res.status}.${missing}`);
        }
      }
    } catch (err: any) {
      console.error("Clerk verify code error:", err);
      setError(err.errors?.[0]?.longMessage || err.errors?.[0]?.message || err.message || "Invalid verification code.");
    } finally {
      setLoading(false);
    }
  };

  const renderVisualMockup = () => {
    switch (slideIndex) {
      case 0:
        return (
          <View style={styles.simpleMockCard}>
            <Text style={styles.simpleMockEmoji}>🥄</Text>
            <Text style={styles.simpleMockBigText}>4.5 tsp</Text>
            <Text style={styles.simpleMockSubText}>Average sugar in sweet snacks</Text>
          </View>
        );
      case 1:
        return (
          <View style={styles.simpleMockCard}>
            <View style={styles.simpleMockRow}>
              <Text style={styles.simpleMockLabel}>Daily Sugar Budget</Text>
              <Text style={styles.simpleMockValue}>6 / 10 tsp</Text>
            </View>
            <View style={styles.mockProgressTrack}>
              <View style={[styles.mockProgressFill, { width: "60%" }]} />
            </View>
          </View>
        );
      case 2:
      default:
        return (
          <View style={styles.simpleMockCard}>
            <Text style={styles.simpleMockEmoji}>🎯</Text>
            <Text style={styles.simpleMockBigText}>Personalized</Text>
            <Text style={styles.simpleMockSubText}>Tailored to your health flags</Text>
          </View>
        );
    }
  };

  if (showGetStarted) {
    return (
      <View style={styles.simpleOnboardingContainer}>
        {/* Logo and Tagline */}
        <View style={[styles.simpleOnboardingHeader, { paddingTop: insets.top + space.xl }]}>
          <Text style={styles.simpleOnboardingLogo}>🥄 TeaSpoon</Text>
          <Text style={styles.simpleOnboardingTagline}>Know it in teaspoons, not grams</Text>
        </View>

        {/* Dynamic visual preview */}
        <Animated.View
          style={[
            styles.simpleVisualWrapper,
            { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
          ]}
        >
          {renderVisualMockup()}
        </Animated.View>

        {/* Content Area */}
        <View style={styles.simpleContentWrapper}>
          <ScrollView
            style={styles.cardScroll}
            contentContainerStyle={styles.cardScrollContent}
            showsVerticalScrollIndicator={false}
          >
            <Text style={styles.simpleOnboardingTitle}>
              {ONBOARDING_SLIDES[slideIndex].title.replace("\n", " ")}
            </Text>

            {slideIndex !== 2 ? (
              <Text style={styles.simpleOnboardingSubtitle}>
                {ONBOARDING_SLIDES[slideIndex].subtitle}
              </Text>
            ) : (
              <View style={styles.goalsContainer}>
                {GOAL_OPTIONS.map((goal) => {
                  const active = healthFlags.includes(goal.key);
                  return (
                    <Pressable
                      key={goal.key}
                      style={[styles.goalRow, active && styles.goalRowActive]}
                      onPress={() => toggleHealthFlag(goal.key)}
                    >
                      <Text style={styles.goalEmoji}>{goal.emoji}</Text>
                      <View style={styles.goalTextWrap}>
                        <Text style={[styles.goalLabel, active && styles.goalLabelActive]}>
                          {goal.label}
                        </Text>
                        <Text style={[styles.goalDesc, active && styles.goalDescActive]}>
                          {goal.desc}
                        </Text>
                      </View>
                      <View style={[styles.goalCheckbox, active && styles.goalCheckboxActive]}>
                        {active && <Text style={styles.goalCheckIcon}>✓</Text>}
                      </View>
                    </Pressable>
                  );
                })}
              </View>
            )}
          </ScrollView>
        </View>

        {/* Footer Area */}
        <View style={[styles.simpleOnboardingFooter, { paddingBottom: insets.bottom + space.lg }]}>
          {/* Carousel dots indicator */}
          <View style={styles.onboardingDots}>
            {ONBOARDING_SLIDES.map((_, idx) => (
              <Pressable
                key={idx}
                style={[
                  styles.onboardingDot,
                  slideIndex === idx ? styles.onboardingDotActive : styles.onboardingDotInactive,
                ]}
                onPress={() => goToSlide(idx)}
              />
            ))}
          </View>

          {/* Large main action button */}
          <Pressable
            style={({ pressed }) => [styles.onboardingBtn, pressed && styles.onboardingBtnPressed]}
            onPress={() => {
              console.log("GET STARTED BUTTON TAPPED, slideIndex:", slideIndex);
              if (slideIndex < ONBOARDING_SLIDES.length - 1) {
                goToSlide(slideIndex + 1);
              } else {
                console.log("Setting showGetStarted to false!");
                setShowGetStarted(false);
              }
            }}
          >
            <Text style={styles.onboardingBtnText}>
              {slideIndex === ONBOARDING_SLIDES.length - 1 ? "Get Started" : "Continue"}
            </Text>
          </Pressable>

          {/* Skip / Sign in Option */}
          <Pressable
            onPress={() => setShowGetStarted(false)}
            style={styles.simpleOnboardingSkip}
          >
            <Text style={styles.simpleOnboardingSkipText}>
              Already have an account? Sign In
            </Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        <View style={[styles.inner, { paddingTop: insets.top + space.xl, paddingBottom: insets.bottom + space.lg }]}>
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

                <Pressable
                  style={styles.backButton}
                  onPress={() => {
                    setShowGetStarted(true);
                    setError(null);
                  }}
                  disabled={loading}
                >
                  <Text style={styles.backButtonText}>← Back to onboarding</Text>
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
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: "center",
  },
  inner: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: space.lg,
  },
  header: {
    alignItems: "center",
    marginBottom: space.xl,
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
    paddingVertical: 14,
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

  // Onboarding container
  onboardingContainer: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  onboardingTop: {
    flex: 1.2,
    justifyContent: "flex-start",
    alignItems: "center",
    position: "relative",
  },
  onboardingImg: {
    ...StyleSheet.absoluteFillObject,
    width: "100%",
    height: "100%",
  },
  onboardingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(27, 26, 23, 0.4)", // Dark overlay to make mockup readable
  },
  onboardingLogoWrap: {
    marginTop: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 10,
  },
  onboardingLogoText: {
    fontSize: 28,
    fontWeight: weight.black,
    color: colors.white,
    textShadowColor: "rgba(0,0,0,0.5)",
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 6,
  },

  // Mock visuals styles
  mockPreviewWrapper: {
    flex: 1,
    width: "100%",
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: space.lg,
    marginTop: 20,
    zIndex: 5,
  },
  mockCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: space.md,
    width: "85%",
    maxWidth: 320,
    ...shadow.card,
  },
  mockHeader: {
    marginBottom: space.sm,
  },
  mockProductTitle: {
    fontSize: font.title,
    fontWeight: weight.bold,
    color: colors.ink,
  },
  mockProductSub: {
    fontSize: font.small,
    color: colors.inkSoft,
    marginTop: 2,
  },
  mockHero: {
    flexDirection: "row",
    alignItems: "baseline",
    marginVertical: space.xs,
  },
  mockBigText: {
    fontSize: font.hero - 15,
    fontWeight: weight.black,
    color: colors.accent,
  },
  mockUnitText: {
    fontSize: font.body,
    fontWeight: weight.bold,
    color: colors.inkSoft,
    marginLeft: 6,
  },
  mockChips: {
    flexDirection: "row",
    gap: 8,
    marginBottom: space.md,
  },
  mockChip: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radius.sm,
  },
  mockChipText: {
    fontSize: font.tiny,
    fontWeight: weight.bold,
    color: colors.ink,
  },
  mockSwapCard: {
    backgroundColor: colors.greenSoft,
    borderRadius: radius.sm,
    padding: space.sm,
    borderWidth: 1,
    borderColor: colors.green,
  },
  mockSwapLabel: {
    fontSize: font.tiny,
    color: colors.green,
    fontWeight: weight.bold,
  },
  mockSwapRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 4,
  },
  mockSwapName: {
    fontSize: font.small,
    fontWeight: weight.bold,
    color: colors.ink,
  },
  mockSwapDiff: {
    fontSize: font.small,
    fontWeight: weight.bold,
    color: colors.green,
  },
  mockProgressTrack: {
    height: 10,
    backgroundColor: colors.accentTrack,
    borderRadius: 5,
    marginVertical: space.xs,
    overflow: "hidden",
  },
  mockProgressFill: {
    height: "100%",
    backgroundColor: colors.accent,
  },
  mockProgressWarning: {
    fontSize: font.small,
    fontWeight: weight.semibold,
    color: colors.danger,
    marginBottom: space.sm,
  },
  mockGrid: {
    flexDirection: "row",
    gap: 12,
  },
  mockGridItem: {
    flex: 1,
    backgroundColor: colors.bg,
    padding: space.xs,
    borderRadius: radius.sm,
    alignItems: "center",
  },
  mockGridLabel: {
    fontSize: font.tiny,
    color: colors.inkSoft,
  },
  mockGridValue: {
    fontSize: font.body,
    fontWeight: weight.bold,
    color: colors.ink,
    marginTop: 2,
  },
  mockShieldContainer: {
    alignItems: "center",
    justifyContent: "center",
    width: "85%",
  },
  mockShieldOuter: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: "rgba(242, 137, 92, 0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
  mockShieldInner: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    ...shadow.floating,
  },
  mockShieldEmoji: {
    fontSize: 38,
  },
  mockShieldBadges: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 8,
    marginTop: 16,
  },
  mockShieldBadge: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    borderRadius: radius.pill,
    paddingHorizontal: 12,
    paddingVertical: 6,
    ...shadow.card,
  },
  mockShieldBadgeText: {
    fontSize: font.small,
    fontWeight: weight.bold,
    color: colors.ink,
  },

  // Onboarding lower card
  onboardingCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderTopLeftRadius: 36,
    borderTopRightRadius: 36,
    paddingHorizontal: space.lg,
    paddingTop: space.lg,
    alignItems: "center",
    ...shadow.floating,
    marginTop: -24,
  },
  cardScroll: {
    width: "100%",
    flex: 1,
  },
  cardScrollContent: {
    alignItems: "center",
    paddingBottom: space.md,
  },
  onboardingTitle: {
    fontSize: 26,
    fontWeight: weight.black,
    color: colors.ink,
    textAlign: "center",
    lineHeight: 32,
    marginBottom: space.sm,
    marginTop: space.xs,
  },
  onboardingSubtitle: {
    fontSize: font.body,
    fontWeight: weight.medium,
    color: colors.inkSoft,
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: space.xs,
  },
  onboardingDots: {
    flexDirection: "row",
    gap: 8,
    alignItems: "center",
    marginVertical: space.sm,
  },
  onboardingDot: {
    height: 8,
    borderRadius: 4,
  },
  onboardingDotActive: {
    width: 24,
    backgroundColor: colors.accent,
  },
  onboardingDotInactive: {
    width: 8,
    backgroundColor: colors.inkFaint,
    opacity: 0.4,
  },
  onboardingBtn: {
    width: "100%",
    backgroundColor: colors.dark,
    borderRadius: radius.pill,
    paddingVertical: 15,
    alignItems: "center",
    justifyContent: "center",
    marginTop: space.xs,
    ...shadow.floating,
  },
  onboardingBtnPressed: {
    backgroundColor: colors.darkSoft,
  },
  onboardingBtnText: {
    color: colors.white,
    fontSize: font.body,
    fontWeight: weight.bold,
  },
  onboardingSocialLabel: {
    fontSize: font.small,
    fontWeight: weight.semibold,
    color: colors.inkSoft,
    marginTop: space.md,
    marginBottom: space.xs,
  },
  onboardingSocialRow: {
    flexDirection: "row",
    gap: 16,
    marginBottom: space.xs,
  },
  onboardingSocialCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
    ...shadow.card,
  },
  onboardingSocialCirclePressed: {
    backgroundColor: colors.surfaceSunken,
  },

  // Goals checklist interactive elements
  goalsContainer: {
    width: "100%",
    marginTop: space.xs,
    gap: 8,
  },
  goalRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    paddingVertical: 10,
    paddingHorizontal: space.md,
    borderWidth: 1.5,
    borderColor: "transparent",
  },
  goalRowActive: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
  },
  goalEmoji: {
    fontSize: 22,
    marginRight: 10,
  },
  goalTextWrap: {
    flex: 1,
  },
  goalLabel: {
    fontSize: font.body,
    fontWeight: weight.bold,
    color: colors.ink,
  },
  goalLabelActive: {
    color: colors.accentDeep,
  },
  goalDesc: {
    fontSize: font.tiny,
    color: colors.inkSoft,
    marginTop: 1,
  },
  goalDescActive: {
    color: colors.ink,
  },
  goalCheckbox: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: colors.inkFaint,
    alignItems: "center",
    justifyContent: "center",
  },
  goalCheckboxActive: {
    backgroundColor: colors.accent,
    borderColor: colors.accent,
  },
  goalCheckIcon: {
    color: colors.white,
    fontSize: 12,
    fontWeight: weight.bold,
  },

  // Simplified Onboarding Styles
  simpleOnboardingContainer: {
    flex: 1,
    backgroundColor: colors.surface,
    paddingHorizontal: space.lg,
  },
  simpleOnboardingHeader: {
    alignItems: "center",
    marginBottom: space.lg,
  },
  simpleOnboardingLogo: {
    fontSize: font.h1,
    fontWeight: weight.black,
    color: colors.ink,
    letterSpacing: -0.5,
  },
  simpleOnboardingTagline: {
    fontSize: font.small,
    color: colors.inkSoft,
    fontWeight: weight.semibold,
    marginTop: space.xs,
  },
  simpleVisualWrapper: {
    height: 140,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: space.md,
  },
  simpleMockCard: {
    backgroundColor: colors.surfaceAlt,
    borderRadius: radius.md,
    padding: space.md,
    width: "100%",
    maxWidth: 320,
    alignItems: "center",
    ...shadow.card,
    borderWidth: 1,
    borderColor: colors.line,
  },
  simpleMockEmoji: {
    fontSize: font.big,
    marginBottom: space.xs,
  },
  simpleMockBigText: {
    fontSize: font.h2,
    fontWeight: weight.black,
    color: colors.accent,
  },
  simpleMockSubText: {
    fontSize: font.small,
    color: colors.inkSoft,
    marginTop: 4,
    textAlign: "center",
  },
  simpleMockRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    width: "100%",
    marginBottom: space.xs,
  },
  simpleMockLabel: {
    fontSize: font.body,
    fontWeight: weight.bold,
    color: colors.ink,
  },
  simpleMockValue: {
    fontSize: font.body,
    fontWeight: weight.bold,
    color: colors.accent,
  },
  simpleContentWrapper: {
    flex: 1,
    width: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  simpleOnboardingTitle: {
    fontSize: font.h2,
    fontWeight: weight.black,
    color: colors.ink,
    textAlign: "center",
    lineHeight: 28,
    marginBottom: space.sm,
  },
  simpleOnboardingSubtitle: {
    fontSize: font.body,
    fontWeight: weight.medium,
    color: colors.inkSoft,
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: space.sm,
  },
  simpleOnboardingFooter: {
    alignItems: "center",
    width: "100%",
    marginTop: space.md,
  },
  simpleOnboardingSkip: {
    marginTop: space.md,
    paddingVertical: space.xs,
  },
  simpleOnboardingSkipText: {
    color: colors.inkSoft,
    fontSize: font.small,
    fontWeight: weight.bold,
  },
});

