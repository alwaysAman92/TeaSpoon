// Default Expo Metro config. Expo SDK 50+ resolves the `@/*` tsconfig path
// aliases automatically (experiments.tsconfigPaths defaults to true).
const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);

module.exports = config;
