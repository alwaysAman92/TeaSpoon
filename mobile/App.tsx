import { ClerkProvider, SignedIn, SignedOut, useAuth } from "@clerk/clerk-expo";
import { createBottomTabNavigator, type BottomTabBarProps } from "@react-navigation/bottom-tabs";
import { DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import * as SecureStore from "expo-secure-store";
import { StatusBar } from "expo-status-bar";
import React, { useEffect } from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider, useSafeAreaInsets } from "react-native-safe-area-context";

import { setClerkTokenGetter } from "@/api/client";
import type { RootStackParamList, TabsParamList } from "@/navigation";
import { CaptureScreen } from "@/screens/CaptureScreen";
import { DashboardScreen } from "@/screens/DashboardScreen";
import { ResultScreen } from "@/screens/ResultScreen";
import { ScanScreen } from "@/screens/ScanScreen";
import { SettingsScreen } from "@/screens/SettingsScreen";
import { SignInScreen } from "@/screens/SignInScreen";
import { AppProvider } from "@/store/AppContext";
import { colors, radius, shadow, weight } from "@/theme";

const Tab = createBottomTabNavigator<TabsParamList>();
const Stack = createNativeStackNavigator<RootStackParamList>();

const CLERK_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;

// Clerk token cache for native secure storage.
const tokenCache =
  Platform.OS !== "web"
    ? {
        getToken: (key: string) => SecureStore.getItemAsync(key),
        saveToken: (key: string, value: string) => SecureStore.setItemAsync(key, value),
      }
    : undefined;

const GLYPHS: Record<keyof TabsParamList, string> = {
  Dashboard: "◎",
  Scan: "＋",
  Settings: "⚙",
};

function FloatingTabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.tabWrap, { paddingBottom: insets.bottom ? insets.bottom : 14 }]} pointerEvents="box-none">
      <View style={styles.tabBar}>
        {state.routes.map((route, index) => {
          const focused = state.index === index;
          const name = route.name as keyof TabsParamList;
          const isScan = name === "Scan";

          const onPress = () => {
            const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });
            if (!focused && !event.defaultPrevented) {
              navigation.navigate(route.name);
            }
          };

          if (isScan) {
            return (
              <Pressable key={route.key} onPress={onPress} style={styles.scanButton}>
                <Text style={styles.scanGlyph}>＋</Text>
              </Pressable>
            );
          }

          return (
            <Pressable key={route.key} onPress={onPress} style={styles.tabItem}>
              <Text style={[styles.tabGlyph, focused && styles.tabGlyphActive]}>{GLYPHS[name]}</Text>
              <Text style={[styles.tabLabel, focused && styles.tabLabelActive]}>
                {name === "Dashboard" ? "Today" : name}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function Tabs() {
  return (
    <Tab.Navigator
      tabBar={(props) => <FloatingTabBar {...props} />}
      screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: colors.bg } }}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Scan" component={ScanScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

const navTheme = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, background: colors.bg, card: colors.bg, text: colors.ink, border: colors.line },
};

/** Bridges Clerk auth into the API client once a session is active. */
function AuthBridge({ children }: { children: React.ReactNode }) {
  const { getToken } = useAuth();

  useEffect(() => {
    setClerkTokenGetter(() => getToken());
  }, [getToken]);

  return <>{children}</>;
}

function AppInner() {
  const innerContent = (
    <Stack.Navigator screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.bg } }}>
      <Stack.Screen name="Tabs" component={Tabs} />
      <Stack.Screen
        name="Result"
        component={ResultScreen}
        options={{ presentation: "modal", animation: "slide_from_bottom" }}
      />
      <Stack.Screen
        name="Capture"
        component={CaptureScreen}
        options={{ presentation: "modal", animation: "slide_from_bottom" }}
      />
    </Stack.Navigator>
  );

  return (
    <SafeAreaProvider>
      <AppProvider>
        <StatusBar style="dark" />
        {CLERK_KEY ? (
          <>
            <SignedIn>
              <NavigationContainer theme={navTheme}>
                {innerContent}
              </NavigationContainer>
            </SignedIn>
            <SignedOut>
              <SignInScreen />
            </SignedOut>
          </>
        ) : (
          <NavigationContainer theme={navTheme}>
            {innerContent}
          </NavigationContainer>
        )}
      </AppProvider>
    </SafeAreaProvider>
  );
}

export default function App() {
  if (CLERK_KEY) {
    return (
      <ClerkProvider publishableKey={CLERK_KEY} tokenCache={tokenCache}>
        <AuthBridge>
          <AppInner />
        </AuthBridge>
      </ClerkProvider>
    );
  }

  // No Clerk key configured — run without auth (local dev).
  return <AppInner />;
}

const styles = StyleSheet.create({
  tabWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    paddingHorizontal: 20,
  },
  tabBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    backgroundColor: colors.dark,
    borderRadius: radius.pill,
    height: 64,
    width: "100%",
    maxWidth: 420,
    paddingHorizontal: 18,
    ...shadow.floating,
  },
  tabItem: { alignItems: "center", justifyContent: "center", flex: 1 },
  tabGlyph: { fontSize: 20, color: colors.onDarkMuted },
  tabGlyphActive: { color: colors.accent },
  tabLabel: { fontSize: 10, color: colors.onDarkMuted, marginTop: 2, fontWeight: weight.semibold },
  tabLabelActive: { color: colors.onDark },
  scanButton: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    marginTop: -24,
    borderWidth: 5,
    borderColor: colors.bg,
    ...shadow.floating,
  },
  scanGlyph: { color: colors.white, fontSize: 28, fontWeight: weight.bold, lineHeight: 30 },
});
