/**
 * Cliente de calibración para Sensus AI.
 * Coordina el proceso de calibración métrica del estimador de profundidad.
 *
 * Flujo:
 *   1. getCalibrationStatus()   → muestra estado actual
 *   2. takeSample(imageUri)     → envía foto y recibe raw_depth del centro
 *   3. addPoint(rawDepth, realM)→ registra par (modelo, real)
 *   4. saveCalibration()        → calcula regresión y guarda en el servidor
 *   5. resetCalibration()       → vuelve a a=1, b=0
 */

import { getApiBaseUrl } from "./sensusClient";

// Convierte una URI de imagen local a base64 usando fetch
async function uriToBase64(imageUri) {
  const response = await fetch(imageUri);
  const blob = await response.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      // reader.result es "data:image/jpeg;base64,XXXX"
      const base64 = reader.result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Obtiene el estado actual de la calibración desde el servidor.
 * @returns {{ a, b, formula, calibrated, points_saved, points_session, depth_available }}
 */
export async function getCalibrationStatus() {
  const res = await fetch(`${getApiBaseUrl()}/api/calibration/status`);
  if (!res.ok) throw new Error(`Error al obtener estado: ${res.status}`);
  return res.json();
}

/**
 * Envía una foto al servidor y recibe la profundidad cruda del centro.
 * @param {string} imageUri - URI local de la imagen (file://...)
 * @returns {{ raw_depth: number, points_session: number }}
 */
export async function takeSample(imageUri) {
  const image_b64 = await uriToBase64(imageUri);
  const res = await fetch(`${getApiBaseUrl()}/api/calibration/sample`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_b64 }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Error al tomar muestra (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Registra un par (raw_depth, real_m) en la sesión del servidor.
 * @param {number} rawDepth - Valor crudo devuelto por takeSample
 * @param {number} realM    - Distancia real medida en metros
 * @returns {{ ok, points_session, points, ready_to_save }}
 */
export async function addCalibrationPoint(rawDepth, realM) {
  const res = await fetch(`${getApiBaseUrl()}/api/calibration/point`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_depth: rawDepth, real_m: realM }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Error al agregar punto (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Elimina los puntos de la sesión actual sin guardar.
 */
export async function clearCalibrationPoints() {
  const res = await fetch(`${getApiBaseUrl()}/api/calibration/points`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Error al limpiar puntos: ${res.status}`);
  return res.json();
}

/**
 * Calcula la regresión lineal con los puntos de sesión y guarda calibracion.json.
 * @returns {{ ok, a, b, formula, points_used, mae_m, points_detail }}
 */
export async function saveCalibration() {
  const res = await fetch(`${getApiBaseUrl()}/api/calibration/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Error al guardar calibración (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Restablece la calibración a valores neutros (a=1, b=0).
 */
export async function resetCalibration() {
  const res = await fetch(`${getApiBaseUrl()}/api/calibration/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`Error al resetear calibración: ${res.status}`);
  return res.json();
}
