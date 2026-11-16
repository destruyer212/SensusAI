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
      permissions: ["CAMERA", "RECORD_AUDIO"],
      usesCleartextTraffic: true,
    },
    extra: {
      apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL || "http://35.153.208.142:8000",
      eas: {
        projectId: "d850ac17-8ba5-4676-b1d5-483c42890e90",
      },
    },
    plugins: ["expo-status-bar", "react-native-vision-camera"],
  },
};
