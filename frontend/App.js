import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  Vibration,
  View,
} from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as Speech from "expo-speech";
import { StatusBar as ExpoStatusBar } from "expo-status-bar";

import {
  analyzeScene,
  getApiBaseUrl,
  getEmergencyGuidance,
  getRoute,
  interpretCommand,
  resolveQr,
} from "./src/api/sensusClient";
import { colors } from "./src/theme/colors";

const OFFICE_TEST_QR = "SENSUS:office_demo:office_entrance";
const REALTIME_MAX_RESPONSE_AGE_MS = 8000;
const REALTIME_INTERVALS = {
  clear: 9000,
  notice: 6500,
  caution: 3800,
  danger: 2600,
  unknown: 7000,
};
const MIN_REPEAT_SPEECH_MS = 12000;

export default function App() {
  const cameraRef = useRef(null);
  const realtimeTimer = useRef(null);
  const isAnalyzingRef = useRef(false);
  const realtimeActiveRef = useRef(false);
  const activeTaskRef = useRef("navigation");
  const requestSeqRef = useRef(0);
  const lastSpokenRef = useRef({ text: "", at: 0 });
  const lastRiskRef = useRef("unknown");
  const [permission, requestPermission] = useCameraPermissions();
  const [isRealtime, setIsRealtime] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [cameraFacing, setCameraFacing] = useState("back");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [status, setStatus] = useState("Camara pendiente");
  const [lastResult, setLastResult] = useState("Concede permiso de camara para iniciar Sensus AI.");
  const [currentLocation, setCurrentLocation] = useState(null);
  const [detections, setDetections] = useState([]);
  const [riskLevel, setRiskLevel] = useState("unknown");
  const [activeTask, setActiveTask] = useState("navigation");

  useEffect(() => {
    activeTaskRef.current = activeTask;
  }, [activeTask]);

  useEffect(() => {
    if (permission && !permission.granted && permission.canAskAgain) {
      requestPermission();
    }

    return () => {
      if (realtimeTimer.current) clearInterval(realtimeTimer.current);
      realtimeActiveRef.current = false;
      Speech.stop();
    };
  }, [permission, requestPermission]);

  function speak(text, { force = false, riskLevelOverride = "unknown" } = {}) {
    if (!voiceEnabled) return;
    const normalized = text.trim().toLowerCase();
    const now = Date.now();
    const isUrgent = ["caution", "danger"].includes(riskLevelOverride);
    const isRepeat = normalized === lastSpokenRef.current.text;
    const tooSoon = now - lastSpokenRef.current.at < MIN_REPEAT_SPEECH_MS;

    if (!force && isRepeat && tooSoon && !isUrgent) return;

    lastSpokenRef.current = { text: normalized, at: now };
    Speech.stop();
    Speech.speak(text, {
      language: "es-PE",
      rate: 1,
      pitch: 1,
    });
  }

  function handleAnalysisResult(result) {
    const nextDetections = Array.isArray(result.detections) ? result.detections : [];
    const nextRisk = result.risk_level || "unknown";
    setLastResult(result.text);
    setDetections(nextDetections);
    setRiskLevel(nextRisk);
    lastRiskRef.current = nextRisk;
    setStatus(result.mode === "gemini" ? `IA ${nextRisk}` : "Modo demo");

    if (["caution", "danger"].includes(nextRisk) || result.action === "stop") {
      Vibration.vibrate([0, 180, 80, 180]);
    }

    speak(result.text, {
      force: result.action === "stop" || nextRisk === "danger",
      riskLevelOverride: nextRisk,
    });
  }

  async function scanScene(taskOverride = activeTaskRef.current, source = "manual") {
    if (!cameraRef.current || isAnalyzingRef.current) return;
    if (!isCameraReady) {
      const message = "La camara aun no esta lista. Espera un momento e intenta otra vez.";
      setLastResult(message);
      setStatus("Camara cargando");
      speak(message);
      return;
    }

    try {
      const requestId = requestSeqRef.current + 1;
      requestSeqRef.current = requestId;
      const startedAt = Date.now();
      isAnalyzingRef.current = true;
      setIsAnalyzing(true);
      setStatus("Analizando entorno");
      const photo = await cameraRef.current.takePictureAsync({
        quality: source === "realtime" ? 0.34 : 0.5,
        skipProcessing: true,
      });

      const result = await analyzeScene(photo.uri, taskOverride);
      const responseAge = Date.now() - startedAt;
      if (requestId !== requestSeqRef.current) return;
      if (source === "realtime" && responseAge > REALTIME_MAX_RESPONSE_AGE_MS) {
        setStatus("Respuesta tarde descartada");
        return;
      }
      handleAnalysisResult(result);
    } catch (error) {
      console.error(error);
      const shortError = error instanceof Error ? error.message.slice(0, 90) : "error desconocido";
      const message = `No pude analizar la escena. Detente y vuelve a intentar. ${shortError}`;
      setLastResult(message);
      setStatus("Error de analisis");
      speak(message);
    } finally {
      isAnalyzingRef.current = false;
      setIsAnalyzing(false);
    }
  }

  function testVoice() {
    const message = "Sensus voz activa. Si escuchas esto, el audio funciona.";
    setLastResult(message);
    setStatus("Probando voz");
    speak(message);
  }

  function findKeys() {
    setActiveTask("find_keys");
    setStatus("Buscando llave");
    scanScene("find_keys");
  }

  async function runCommand(commandText) {
    try {
      setStatus("Escuchando comando");
      const command = await interpretCommand(commandText, currentLocation?.site?.id, currentLocation?.landmark?.id);
      setLastResult(command.text);
      speak(command.text, { force: true });

      if (command.intent === "find_object" || command.intent === "scan_scene") {
        setActiveTask(command.task);
        await scanScene(command.task);
        return;
      }

      if (command.intent === "route") {
        if (!currentLocation) {
          setStatus("Falta ubicacion");
          return;
        }

        const route = await getRoute(currentLocation.site.id, currentLocation.landmark.id, command.destination_id);
        setLastResult(route.text);
        speak(route.text, { force: true });
        setStatus("Ruta por comando");
        return;
      }

      if (command.intent === "emergency") {
        await emergencyMode();
      }
    } catch (error) {
      const message = "No pude ejecutar el comando de voz.";
      setLastResult(message);
      setStatus("Comando fallo");
      speak(message, { force: true });
    }
  }

  function flipCamera() {
    setIsCameraReady(false);
    setCameraFacing((current) => (current === "back" ? "front" : "back"));
    setStatus("Cambiando camara");
  }

  async function simulateOfficeQr() {
    try {
      setStatus("Leyendo QR");
      const result = await resolveQr(OFFICE_TEST_QR);
      setCurrentLocation(result);
      setLastResult(result.text);
      speak(result.text);
      setStatus("Ubicacion detectada");
    } catch (error) {
      const message = "No pude reconocer este QR.";
      setLastResult(message);
      speak(message);
      setStatus("QR no registrado");
    }
  }

  async function routeToMensBathroom() {
    if (!currentLocation) {
      const message = "Primero escanea un QR o usa el QR de prueba.";
      setLastResult(message);
      speak(message);
      return;
    }

    try {
      setStatus("Calculando ruta");
      const result = await getRoute(
        currentLocation.site.id,
        currentLocation.landmark.id,
        currentLocation.site.id === "office_demo" ? "office_mens_bathroom" : "u_p7_mens_bathroom"
      );
      setLastResult(result.text);
      speak(result.text);
      setStatus("Ruta lista");
    } catch (error) {
      const message = "No encontre una ruta segura para ese destino.";
      setLastResult(message);
      speak(message);
      setStatus("Ruta no encontrada");
    }
  }

  async function emergencyMode() {
    if (!currentLocation) {
      const message = "Modo emergencia. Detente y pide apoyo cercano. No tengo una ubicacion confirmada.";
      setLastResult(message);
      speak(message);
      setStatus("Emergencia sin ubicacion");
      return;
    }

    try {
      setStatus("Modo emergencia");
      const result = await getEmergencyGuidance(currentLocation.site.id, currentLocation.landmark.id);
      setLastResult(result.text);
      speak(result.text);
    } catch (error) {
      const message = "Modo emergencia. Detente y pide apoyo cercano.";
      setLastResult(message);
      speak(message);
    }
  }

  function toggleRealtime() {
    const next = !isRealtime;
    setIsRealtime(next);
    realtimeActiveRef.current = next;

    if (realtimeTimer.current) {
      clearTimeout(realtimeTimer.current);
      realtimeTimer.current = null;
    }

    if (next) {
      setStatus("Tiempo real iniciando");
      scanScene(activeTaskRef.current, "realtime").finally(scheduleRealtimeScan);
    } else {
      requestSeqRef.current += 1;
      setStatus("Tiempo real detenido");
    }
  }

  function scheduleRealtimeScan() {
    if (!realtimeActiveRef.current) return;
    const delay = REALTIME_INTERVALS[lastRiskRef.current] || REALTIME_INTERVALS.unknown;
    realtimeTimer.current = setTimeout(async () => {
      if (!realtimeActiveRef.current) return;
      await scanScene(activeTaskRef.current, "realtime");
      scheduleRealtimeScan();
    }, delay);
  }

  if (!permission) {
    return <LoadingScreen text="Preparando permisos" />;
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.permissionScreen}>
        <ExpoStatusBar style="light" />
        <Text style={styles.brand}>Sensus AI</Text>
        <Text style={styles.title}>Inteligencia espacial asistida</Text>
        <Text style={styles.permissionText}>
          Sensus necesita la camara para enviar imagenes al backend y recibir una descripcion hablada del entorno.
        </Text>
        <Text style={styles.permissionHint}>API: {getApiBaseUrl()}</Text>
        <Pressable style={styles.primaryButton} onPress={requestPermission}>
          <Text style={styles.primaryButtonText}>Permitir camara</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ExpoStatusBar style="light" />
      <SafeAreaView style={styles.screen}>
        <View style={styles.topBar}>
          <View>
            <Text style={styles.brand}>Sensus AI</Text>
            <Text style={styles.subtitle}>Assistive Spatial Intelligence</Text>
          </View>
          <View style={styles.statusPill}>
            <Text style={styles.statusText}>{status}</Text>
          </View>
        </View>

        <View style={styles.cameraPanel}>
          <CameraView
            ref={cameraRef}
            style={styles.cameraPreview}
            facing={cameraFacing}
            mode="picture"
            active={permission.granted}
            onCameraReady={() => {
              setIsCameraReady(true);
              setStatus("Camara lista");
            }}
            onMountError={(event) => {
              const message = `No pude abrir la camara: ${event.nativeEvent?.message || "permiso o dispositivo no disponible"}`;
              setIsCameraReady(false);
              setStatus("Camara no disponible");
              setLastResult(message);
              speak(message);
            }}
          />
          <View style={styles.cameraBadge}>
            <Text style={styles.cameraBadgeText}>
              {isRealtime ? "Tiempo real activo" : isCameraReady ? "Visor camara" : "Cargando camara"}
            </Text>
          </View>
        </View>

        <ScrollView style={styles.bottomScroll} contentContainerStyle={styles.bottomStack}>
          {!isCameraReady ? (
            <View style={styles.cameraNotice}>
              <ActivityIndicator color={colors.accent} />
              <Text style={styles.cameraNoticeText}>Cargando camara. Si la pantalla sigue negra, revisa permisos de Expo Go.</Text>
            </View>
          ) : null}

          <View style={styles.resultPanel}>
            <Text style={styles.resultLabel}>Ultima lectura</Text>
            <Text style={styles.resultText}>{lastResult}</Text>
          </View>

          <View style={styles.debugPanel}>
            <View style={styles.debugHeader}>
              <Text style={styles.debugTitle}>Detecciones</Text>
              <Text style={styles.riskBadge}>{riskLevel}</Text>
            </View>
            {detections.length > 0 ? (
              <ScrollView style={styles.detectionList}>
                {detections.map((item, index) => (
                  <Text key={`${item.label}-${index}`} style={styles.detectionText}>
                    {item.label || "objeto"} · {item.position || "posicion?"} · {item.distance || "distancia?"} · {item.confidence || "confianza?"}
                  </Text>
                ))}
              </ScrollView>
            ) : (
              <Text style={styles.emptyDetections}>Sin detecciones estructuradas todavia.</Text>
            )}
          </View>

          <View style={styles.controls}>
            <Pressable
              style={[styles.actionButton, isAnalyzing && styles.disabledButton]}
              disabled={isAnalyzing}
              onPress={scanScene}
            >
              {isAnalyzing ? (
                <ActivityIndicator color={colors.inkDark} />
              ) : (
                <Text style={styles.actionButtonText}>Leer ahora</Text>
              )}
            </Pressable>

            <Pressable
              style={[styles.actionButton, styles.secondaryButton, isRealtime && styles.stopButton]}
              onPress={toggleRealtime}
            >
              <Text style={styles.actionButtonText}>{isRealtime ? "Detener" : "Tiempo real 6s"}</Text>
            </Pressable>
          </View>

          <View style={styles.utilityControls}>
            <Pressable style={styles.utilityButton} onPress={findKeys}>
              <Text style={styles.utilityButtonText}>Buscar llave</Text>
            </Pressable>
            <Pressable style={styles.utilityButton} onPress={testVoice}>
              <Text style={styles.utilityButtonText}>Probar voz</Text>
            </Pressable>
            <Pressable style={styles.utilityButton} onPress={flipCamera}>
              <Text style={styles.utilityButtonText}>Voltear</Text>
            </Pressable>
          </View>

          <View style={styles.commandControls}>
            <Pressable style={styles.commandButton} onPress={() => runCommand("Sensus quiero ir al bano")}>
              <Text style={styles.commandButtonText}>Sensus baño</Text>
            </Pressable>
            <Pressable style={styles.commandButton} onPress={() => runCommand("Sensus quiero buscar mis llaves")}>
              <Text style={styles.commandButtonText}>Sensus llaves</Text>
            </Pressable>
            <Pressable style={styles.commandButton} onPress={() => runCommand("Sensus emergencia")}>
              <Text style={styles.commandButtonText}>Sensus ayuda</Text>
            </Pressable>
          </View>

          <View style={styles.spatialControls}>
            <Pressable style={styles.spatialButton} onPress={simulateOfficeQr}>
              <Text style={styles.spatialButtonText}>QR oficina</Text>
            </Pressable>
            <Pressable style={styles.spatialButton} onPress={routeToMensBathroom}>
              <Text style={styles.spatialButtonText}>Bano H</Text>
            </Pressable>
            <Pressable style={[styles.spatialButton, styles.emergencyButton]} onPress={emergencyMode}>
              <Text style={styles.spatialButtonText}>Emergencia</Text>
            </Pressable>
          </View>

          <View style={styles.voiceRow}>
            <Text style={styles.voiceText}>Voz</Text>
            <Switch value={voiceEnabled} onValueChange={setVoiceEnabled} />
          </View>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

function LoadingScreen({ text }) {
  return (
    <SafeAreaView style={styles.permissionScreen}>
      <ActivityIndicator color={colors.accent} size="large" />
      <Text style={styles.permissionText}>{text}</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  screen: {
    flex: 1,
    padding: 18,
    gap: 12,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 12,
  },
  brand: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: "900",
    letterSpacing: 0,
  },
  subtitle: {
    marginTop: 4,
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 0,
  },
  statusPill: {
    maxWidth: 150,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  statusText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "800",
    textAlign: "center",
  },
  cameraPanel: {
    flex: 1,
    minHeight: 270,
    overflow: "hidden",
    borderRadius: 8,
    backgroundColor: "#000",
    borderWidth: 1,
    borderColor: colors.line,
  },
  cameraPreview: {
    flex: 1,
  },
  cameraBadge: {
    position: "absolute",
    left: 10,
    bottom: 10,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  cameraBadgeText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  bottomScroll: {
    maxHeight: "54%",
  },
  bottomStack: {
    gap: 12,
    paddingBottom: 10,
  },
  resultPanel: {
    padding: 18,
    borderRadius: 8,
    backgroundColor: colors.panel,
    borderWidth: 1,
    borderColor: colors.line,
  },
  resultLabel: {
    marginBottom: 8,
    color: colors.accent,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  resultText: {
    color: colors.ink,
    fontSize: 19,
    fontWeight: "800",
    lineHeight: 25,
  },
  debugPanel: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  debugHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  debugTitle: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
  },
  riskBadge: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
  },
  detectionList: {
    maxHeight: 82,
  },
  detectionText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "700",
    lineHeight: 19,
  },
  emptyDetections: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: "700",
  },
  controls: {
    flexDirection: "row",
    gap: 12,
  },
  spatialControls: {
    flexDirection: "row",
    gap: 8,
  },
  utilityControls: {
    flexDirection: "row",
    gap: 8,
  },
  commandControls: {
    flexDirection: "row",
    gap: 8,
  },
  commandButton: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: "rgba(247, 201, 72, 0.18)",
    borderWidth: 1,
    borderColor: colors.warning,
  },
  commandButtonText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "900",
  },
  utilityButton: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: "rgba(71, 215, 172, 0.22)",
    borderWidth: 1,
    borderColor: colors.accent,
  },
  utilityButtonText: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "900",
  },
  spatialButton: {
    flex: 1,
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  spatialButtonText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: "900",
  },
  emergencyButton: {
    backgroundColor: "rgba(255, 107, 107, 0.78)",
  },
  actionButton: {
    flex: 1,
    minHeight: 58,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: colors.accent,
  },
  secondaryButton: {
    backgroundColor: colors.warning,
  },
  stopButton: {
    backgroundColor: colors.danger,
  },
  disabledButton: {
    opacity: 0.65,
  },
  actionButtonText: {
    color: colors.inkDark,
    fontSize: 16,
    fontWeight: "900",
  },
  voiceRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  voiceText: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: "800",
  },
  permissionScreen: {
    flex: 1,
    justifyContent: "center",
    gap: 18,
    padding: 24,
    backgroundColor: colors.bg,
  },
  title: {
    color: colors.ink,
    fontSize: 38,
    fontWeight: "900",
    lineHeight: 42,
  },
  permissionText: {
    color: colors.muted,
    fontSize: 17,
    lineHeight: 24,
  },
  permissionHint: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: "800",
  },
  cameraNotice: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  cameraNoticeText: {
    flex: 1,
    color: colors.ink,
    fontSize: 13,
    fontWeight: "800",
  },
  primaryButton: {
    minHeight: 58,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: colors.accent,
  },
  primaryButtonText: {
    color: colors.inkDark,
    fontSize: 17,
    fontWeight: "900",
  },
});
