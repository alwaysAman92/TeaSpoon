// TeaSpoon design tokens.
// Light, warm-cream aesthetic: soft greige background, near-white rounded cards,
// an orange accent, and a dark floating bottom bar with a central scan button.

export const colors = {
  // Surfaces
  bg: "#ECE5DB", // warm greige app background
  surface: "#FBF8F3", // card / panel
  surfaceAlt: "#FFFFFF",
  surfaceSunken: "#F1EAE0",

  // Text
  ink: "#1C1A17",
  inkSoft: "#7A7064",
  inkFaint: "#A89D8E",

  // Brand
  accent: "#F2895C", // primary orange
  accentDeep: "#ED7344",
  accentSoft: "#FBE0D2",
  accentTrack: "#E4DACB", // empty gauge / track

  // Status
  green: "#3FAE7E",
  greenSoft: "#DCF1E7",
  amber: "#E8A33D",
  danger: "#E0584E",
  dangerSoft: "#F7DCD9",

  // Dark elements (bottom bar, scan screen)
  dark: "#1B1A17",
  darkSoft: "#2A2823",
  onDark: "#F4EFE7",
  onDarkMuted: "#9C9384",

  line: "#E3DACE",
  white: "#FFFFFF",
};

export const space = {
  xs: 6,
  sm: 10,
  md: 16,
  lg: 22,
  xl: 32,
  xxl: 48,
};

export const radius = {
  sm: 12,
  md: 18,
  lg: 26,
  xl: 34,
  pill: 999,
};

export const font = {
  hero: 60,
  big: 44,
  h1: 30,
  h2: 23,
  title: 18,
  body: 15,
  small: 13,
  tiny: 11,
};

export const weight = {
  regular: "400" as const,
  medium: "500" as const,
  semibold: "600" as const,
  bold: "700" as const,
  black: "800" as const,
};

export const shadow = {
  card: {
    shadowColor: "#5B4A36",
    shadowOpacity: 0.1,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 3,
  },
  floating: {
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 10 },
    elevation: 10,
  },
};
