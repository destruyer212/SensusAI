/**
 * CalibrationModal – Pantalla de calibración de profundidad para Sensus AI.
 *
 * Flujo:
 *   1. Se muestra la cámara con una mira central verde.
 *   2. Usuario apunta a un objeto, mide la distancia con cinta métrica.
 *   3. Pulsa "Tomar muestra" → foto → servidor devuelve raw_depth.
 *   4. Usuario ingresa la distancia real medida.
 *   5. Pulsa "Registrar punto" → se guarda el par en el servidor.
 *   6. Repite al menos 2 veces desde distintas distancias.
 *   7. Pulsa "Guardar calibración" → el servidor calcula la regresión y actualiza.
 */

import { useRef, useState, useEffect } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Camera, useCameraDevice } from "react-native-vision-camera";
import {
  getCalibrationStatus,
  takeSample,
  addCalibrationPoint,
  clearCalibrationPoints,
  saveCalibration,
  resetCalibration,
} from "../api/calibrationClient";
import { colors } from "../theme/colors";

export default function CalibrationModal({ visible, onClose }) {
  const cameraRef = useRef(null);
  const device = useCameraDevice("back");

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState("idle"); // idle | sampling | entering | saving | done
  const [status, setStatus] = useState(null);        // estado del servidor
  const [lastRaw, setLastRaw] = useState(null);      // profundidad cruda última muestra
  const [realInput, setRealInput] = useState("");    // distancia real ingresada por el usuario
  const [sessionPoints, setSessionPoints] = useState([]); // [(raw, real), ...]
  const [result, setResult] = useState(null);        // respuesta de /save
  const [errorMsg, setErrorMsg] = useState("");

  // Cargar estado al abrir
  useEffect(() => {
    if (visible) {
      loadStatus();
      setStep("idle");
      setLastRaw(null);
      setRealInput("");
      setResult(null);
      setErrorMsg("");
    }
  }, [visible]);

  async function loadStatus() {
    try {
      const s = await getCalibrationStatus();
      setStatus(s);
      setSessionPoints(s.session_points || []);
    } catch (e) {
      setErrorMsg("No se pudo conectar con el servidor.");
    }
  }

  async function handleTakeSample() {
    if (!cameraRef.current) return;
    setLoading(true);
    setErrorMsg("");
    try {
      const snapshot = await cameraRef.current.takeSnapshot({ quality: 85 });
      const imageUri = snapshot.path.startsWith("file://")
        ? snapshot.path
        : `file://${snapshot.path}`;
      const data = await takeSample(imageUri);
      setLastRaw(data.raw_depth);
      setRealInput("");
      setStep("entering");
    } catch (e) {
      setErrorMsg(`Error al tomar muestra: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddPoint() {
    const realM = parseFloat(realInput.replace(",", "."));
    if (!realM || realM <= 0) {
      setErrorMsg("Ingresa una distancia válida en metros (ej: 1.5).");
      return;
    }
    setLoading(true);
    setErrorMsg("");
    try {
      const data = await addCalibrationPoint(lastRaw, realM);
      setSessionPoints(data.points || []);
      setLastRaw(null);
      setRealInput("");
      setStep("idle");
    } catch (e) {
      setErrorMsg(`Error al registrar punto: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setLoading(true);
    setErrorMsg("");
    setStep("saving");
    try {
      const data = await saveCalibration();
      setResult(data);
      setSessionPoints([]);
      setStep("done");
      await loadStatus();
    } catch (e) {
      setErrorMsg(`Error al guardar: ${e.message}`);
      setStep("idle");
    } finally {
      setLoading(false);
    }
  }

  async function handleClear() {
    setLoading(true);
    try {
      await clearCalibrationPoints();
      setSessionPoints([]);
      setLastRaw(null);
      setRealInput("");
      setStep("idle");
      setResult(null);
    } catch (e) {
      setErrorMsg(`Error al limpiar: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    setLoading(true);
    setErrorMsg("");
    try {
      await resetCalibration();
      setResult(null);
      setSessionPoints([]);
      setStep("idle");
      await loadStatus();
    } catch (e) {
      setErrorMsg(`Error al resetear: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  const canSave = sessionPoints.length >= 2;
  const canSample = step === "idle" || step === "done";

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={s.container}>
        {/* Header */}
        <View style={s.header}>
          <View>
            <Text style={s.title}>Calibrar profundidad</Text>
            <Text style={s.subtitle}>Ajusta la escala métrica a tu cámara</Text>
          </View>
          <Pressable style={s.closeBtn} onPress={onClose}>
            <Text style={s.closeBtnText}>✕ Cerrar</Text>
          </Pressable>
        </View>

        <ScrollView style={s.scroll} contentContainerStyle={s.scrollContent}>

          {/* Estado actual del servidor */}
          {status && (
            <View style={s.statusCard}>
              <Text style={s.cardLabel}>Estado actual</Text>
              <Text style={s.formula}>{status.formula}</Text>
              <Text style={s.statusMeta}>
                {status.calibrated
                  ? `✅ Calibrado · ${status.points_saved} puntos guardados`
                  : "⚠️ Sin calibrar (a=1, b=0)"}
              </Text>
              {!status.depth_available && (
                <Text style={s.warning}>
                  ⚠️ El estimador de profundidad no está disponible en el servidor.
                </Text>
              )}
            </View>
          )}

          {/* Vista de cámara con mira central */}
          <View style={s.cameraContainer}>
            {device ? (
              <Camera
                ref={cameraRef}
                style={s.camera}
                device={device}
                isActive={visible}
                photo={true}
              />
            ) : (
              <View style={[s.camera, s.noCamera]}>
                <Text style={s.noCameraText}>Cámara no disponible</Text>
              </View>
            )}

            {/* Mira central */}
            <View style={s.crosshairOuter} pointerEvents="none">
              <View style={s.crosshairH} />
              <View style={s.crosshairV} />
              <View style={s.crosshairBox} />
            </View>

            {/* Instrucción superpuesta */}
            <View style={s.cameraOverlay} pointerEvents="none">
              <Text style={s.cameraHint}>
                {step === "entering"
                  ? `📏 Raw: ${lastRaw?.toFixed(4)} · Ingresa la distancia real abajo`
                  : "Apunta la mira al objeto y mide la distancia"}
              </Text>
            </View>
          </View>

          {/* Error */}
          {!!errorMsg && (
            <View style={s.errorCard}>
              <Text style={s.errorText}>{errorMsg}</Text>
            </View>
          )}

          {/* Paso: tomar muestra */}
          {canSample && (
            <Pressable
              style={[s.primaryBtn, loading && s.disabledBtn]}
              onPress={handleTakeSample}
              disabled={loading || !status?.depth_available}
            >
              {loading ? (
                <ActivityIndicator color="#000" />
              ) : (
                <Text style={s.primaryBtnText}>📸 Tomar muestra</Text>
              )}
            </Pressable>
          )}

          {/* Paso: ingresar distancia real */}
          {step === "entering" && (
            <View style={s.inputCard}>
              <Text style={s.inputLabel}>
                Profundidad cruda detectada: <Text style={s.rawValue}>{lastRaw?.toFixed(4)}</Text>
              </Text>
              <Text style={s.inputHint}>
                Mide con cinta métrica la distancia desde el celular al objeto central:
              </Text>
              <View style={s.inputRow}>
                <TextInput
                  style={s.textInput}
                  value={realInput}
                  onChangeText={setRealInput}
                  placeholder="Ej: 1.50"
                  placeholderTextColor={colors.muted}
                  keyboardType="decimal-pad"
                  autoFocus
                />
                <Text style={s.inputUnit}>m</Text>
              </View>
              <View style={s.inputButtons}>
                <Pressable
                  style={[s.secondaryBtn, loading && s.disabledBtn]}
                  onPress={handleAddPoint}
                  disabled={loading}
                >
                  <Text style={s.secondaryBtnText}>✅ Registrar punto</Text>
                </Pressable>
                <Pressable
                  style={s.cancelBtn}
                  onPress={() => { setStep("idle"); setLastRaw(null); setRealInput(""); }}
                >
                  <Text style={s.cancelBtnText}>Cancelar</Text>
                </Pressable>
              </View>
            </View>
          )}

          {/* Puntos recolectados en sesión */}
          {sessionPoints.length > 0 && (
            <View style={s.pointsCard}>
              <Text style={s.cardLabel}>
                Puntos en sesión ({sessionPoints.length})
                {sessionPoints.length < 2 ? " — necesitas al menos 2" : " — listo para guardar"}
              </Text>
              {sessionPoints.map((pt, i) => (
                <Text key={i} style={s.pointRow}>
                  #{i + 1}  modelo: {pt.raw?.toFixed(4)}  →  real: {pt.real?.toFixed(2)} m
                </Text>
              ))}
              <View style={s.inputButtons}>
                <Pressable
                  style={[s.saveBtn, !canSave && s.disabledBtn]}
                  onPress={handleSave}
                  disabled={!canSave || loading}
                >
                  {loading && step === "saving" ? (
                    <ActivityIndicator color="#000" />
                  ) : (
                    <Text style={s.saveBtnText}>💾 Guardar calibración</Text>
                  )}
                </Pressable>
                <Pressable style={s.cancelBtn} onPress={handleClear} disabled={loading}>
                  <Text style={s.cancelBtnText}>Limpiar puntos</Text>
                </Pressable>
              </View>
            </View>
          )}

          {/* Resultado exitoso */}
          {step === "done" && result && (
            <View style={s.resultCard}>
              <Text style={s.resultTitle}>✅ Calibración guardada</Text>
              <Text style={s.resultFormula}>{result.formula}</Text>
              <Text style={s.resultMeta}>
                {result.points_used} puntos · Error promedio: {result.mae_m} m
              </Text>
              <View style={s.resultTable}>
                {result.points_detail?.map((pt, i) => (
                  <Text key={i} style={s.resultRow}>
                    #{i + 1} real: {pt.real}m  ajustado: {pt.ajustado}m  error: {pt.error}m
                  </Text>
                ))}
              </View>
              <Pressable
                style={s.secondaryBtn}
                onPress={() => setStep("idle")}
              >
                <Text style={s.secondaryBtnText}>Seguir calibrando</Text>
              </Pressable>
            </View>
          )}

          {/* Instrucciones */}
          <View style={s.instructionsCard}>
            <Text style={s.cardLabel}>Cómo calibrar</Text>
            <Text style={s.instructionStep}>1️⃣  Apunta la mira a un objeto o pared plana.</Text>
            <Text style={s.instructionStep}>2️⃣  Pulsa "Tomar muestra" (el servidor mide la profundidad cruda).</Text>
            <Text style={s.instructionStep}>3️⃣  Mide la distancia real con cinta métrica e ingrésala.</Text>
            <Text style={s.instructionStep}>4️⃣  Pulsa "Registrar punto".</Text>
            <Text style={s.instructionStep}>5️⃣  Repite desde al menos 2 distancias distintas (ej: 0.5m, 1m, 2m).</Text>
            <Text style={s.instructionStep}>6️⃣  Pulsa "Guardar calibración".</Text>
          </View>

          {/* Reset */}
          <Pressable style={s.resetBtn} onPress={handleReset} disabled={loading}>
            <Text style={s.resetBtnText}>↺ Restablecer calibración neutra</Text>
          </Pressable>

        </ScrollView>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    padding: 18,
    paddingTop: 52,
    borderBottomWidth: 1,
    borderBottomColor: colors.line,
  },
  title: { color: colors.ink, fontSize: 22, fontWeight: "900" },
  subtitle: { color: colors.muted, fontSize: 13, fontWeight: "700", marginTop: 2 },
  closeBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  closeBtnText: { color: colors.ink, fontWeight: "800", fontSize: 13 },
  scroll: { flex: 1 },
  scrollContent: { padding: 16, gap: 14, paddingBottom: 40 },

  // Status card
  statusCard: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: colors.panel,
    borderWidth: 1,
    borderColor: colors.line,
    gap: 4,
  },
  cardLabel: { color: colors.accent, fontSize: 11, fontWeight: "900", textTransform: "uppercase", marginBottom: 4 },
  formula: { color: colors.ink, fontSize: 14, fontWeight: "800", fontFamily: "monospace" },
  statusMeta: { color: colors.muted, fontSize: 12, fontWeight: "700" },
  warning: { color: "#f59e0b", fontSize: 12, fontWeight: "700", marginTop: 4 },

  // Camera
  cameraContainer: {
    height: 240,
    borderRadius: 10,
    overflow: "hidden",
    backgroundColor: "#000",
    borderWidth: 1,
    borderColor: colors.line,
  },
  camera: { flex: 1 },
  noCamera: { alignItems: "center", justifyContent: "center" },
  noCameraText: { color: colors.muted, fontWeight: "700" },
  crosshairOuter: {
    position: "absolute",
    top: 0, left: 0, right: 0, bottom: 0,
    alignItems: "center",
    justifyContent: "center",
  },
  crosshairH: {
    position: "absolute",
    width: 60,
    height: 2,
    backgroundColor: "#22c55e",
  },
  crosshairV: {
    position: "absolute",
    width: 2,
    height: 60,
    backgroundColor: "#22c55e",
  },
  crosshairBox: {
    position: "absolute",
    width: 60,
    height: 60,
    borderWidth: 2,
    borderColor: "#22c55e",
    borderRadius: 4,
    backgroundColor: "rgba(34, 197, 94, 0.08)",
  },
  cameraOverlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 8,
    backgroundColor: "rgba(0,0,0,0.55)",
  },
  cameraHint: { color: "#fff", fontSize: 12, fontWeight: "700", textAlign: "center" },

  // Error
  errorCard: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: "rgba(239,68,68,0.15)",
    borderWidth: 1,
    borderColor: "#ef4444",
  },
  errorText: { color: "#ef4444", fontSize: 13, fontWeight: "700" },

  // Buttons
  primaryBtn: {
    minHeight: 52,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 10,
    backgroundColor: colors.accent,
  },
  primaryBtnText: { color: "#000", fontSize: 16, fontWeight: "900" },
  secondaryBtn: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: "rgba(71,215,172,0.22)",
    borderWidth: 1,
    borderColor: colors.accent,
  },
  secondaryBtnText: { color: colors.ink, fontSize: 14, fontWeight: "900" },
  saveBtn: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: "#22c55e",
  },
  saveBtnText: { color: "#000", fontSize: 14, fontWeight: "900" },
  cancelBtn: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
  },
  cancelBtnText: { color: colors.muted, fontSize: 13, fontWeight: "700" },
  disabledBtn: { opacity: 0.45 },
  resetBtn: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ef4444",
    backgroundColor: "rgba(239,68,68,0.08)",
  },
  resetBtnText: { color: "#ef4444", fontSize: 13, fontWeight: "700" },

  // Input
  inputCard: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: colors.panel,
    borderWidth: 1,
    borderColor: colors.accent,
    gap: 8,
  },
  inputLabel: { color: colors.ink, fontSize: 14, fontWeight: "800" },
  rawValue: { color: colors.accent, fontFamily: "monospace" },
  inputHint: { color: colors.muted, fontSize: 12, fontWeight: "700" },
  inputRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  textInput: {
    flex: 1,
    height: 48,
    borderRadius: 8,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: 14,
    color: colors.ink,
    fontSize: 20,
    fontWeight: "800",
  },
  inputUnit: { color: colors.muted, fontSize: 18, fontWeight: "900" },
  inputButtons: { flexDirection: "row", gap: 8, marginTop: 4 },

  // Points list
  pointsCard: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: colors.panel,
    borderWidth: 1,
    borderColor: colors.line,
    gap: 6,
  },
  pointRow: { color: colors.ink, fontSize: 13, fontWeight: "700", fontFamily: "monospace" },

  // Result
  resultCard: {
    padding: 16,
    borderRadius: 10,
    backgroundColor: "rgba(34,197,94,0.1)",
    borderWidth: 1,
    borderColor: "#22c55e",
    gap: 6,
  },
  resultTitle: { color: "#22c55e", fontSize: 16, fontWeight: "900" },
  resultFormula: { color: colors.ink, fontSize: 14, fontWeight: "800", fontFamily: "monospace" },
  resultMeta: { color: colors.muted, fontSize: 12, fontWeight: "700" },
  resultTable: { gap: 3, marginTop: 4 },
  resultRow: { color: colors.ink, fontSize: 12, fontWeight: "700", fontFamily: "monospace" },

  // Instructions
  instructionsCard: {
    padding: 14,
    borderRadius: 10,
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.line,
    gap: 6,
  },
  instructionStep: { color: colors.muted, fontSize: 13, fontWeight: "700", lineHeight: 20 },
});
