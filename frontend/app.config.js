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
      permissions: ["CAMERA", "RECORD_AUDIO", "INTERNET", "ACCESS_NETWORK_STATE"],
      usesCleartextTraffic: true,
    },
    extra: {
      apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL || "http://100.24.55.64:8000",
      eas: {
        projectId: "a986816e-e507-4478-901c-1d5edb815d16",
      },
    },
    plugins: [
      "expo-status-bar",
      ["react-native-vision-camera", { enableFrameProcessors: false }],
    ],
  },
};
