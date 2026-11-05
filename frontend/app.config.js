export default {
  expo: {
    name: "Sensus AI",
    slug: "sensus-ai",
    version: "0.1.0",
    orientation: "portrait",
    userInterfaceStyle: "dark",
    scheme: "sensusai",
    assetBundlePatterns: ["**/*"],
    ios: {
      supportsTablet: true,
      infoPlist: {
        NSCameraUsageDescription: "Sensus AI usa la camara para analizar el entorno en pruebas controladas.",
      },
    },
    android: {
      package: "com.sensusai.mobile",
      permissions: ["CAMERA"],
    },
    extra: {
      apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000",
    },
    plugins: ["expo-status-bar"],
  },
};
