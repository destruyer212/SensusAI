import Constants from "expo-constants";
import * as FileSystem from "expo-file-system/legacy";
const configuredUrl = Constants.expoConfig?.extra?.apiBaseUrl;
const API_BASE_URL = configuredUrl || "http://localhost:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function getVisionCapabilities() {
  const response = await fetch(`${API_BASE_URL}/api/vision/capabilities`, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`Sensus API capabilities error: ${response.status}`);
  return response.json();
}

export async function fastDetectScene(imageUri, sessionId = "mobile-default") {
  return uploadImage("/api/vision/fast-detect", imageUri, { session_id: sessionId });
}

export async function analyzeScene(imageUri, task = "navigation") {
  return uploadImage("/api/vision/analyze", imageUri, { task });
}

async function uploadImage(path, imageUri, query = {}) {
  const queryString = new URLSearchParams(query).toString();
  const result = await FileSystem.uploadAsync(
    `${API_BASE_URL}${path}?${queryString}`,
    imageUri,
    {
      uploadType: FileSystem.FileSystemUploadType.MULTIPART,
      fieldName: "image",
      mimeType: "image/jpeg",
    },
  );

  if (result.status < 200 || result.status >= 300) {
    throw new Error(`Sensus API error: ${result.status} ${result.body || ""}`);
  }
  return JSON.parse(result.body);
}

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Sensus API error: ${response.status} ${detail}`);
  }

  return response.json();
}

export async function resolveQr(qrCode) {
  return postJson("/api/spatial/qr", { qr_code: qrCode });
}

export async function getRoute(siteId, fromLandmarkId, destinationId) {
  return postJson("/api/spatial/route", {
    site_id: siteId,
    from_landmark_id: fromLandmarkId,
    destination_id: destinationId,
  });
}

export async function getEmergencyGuidance(siteId, fromLandmarkId) {
  return postJson("/api/spatial/emergency", {
    site_id: siteId,
    from_landmark_id: fromLandmarkId,
  });
}

export async function interpretCommand(text, siteId, landmarkId) {
  return postJson("/api/command/interpret", {
    text,
    site_id: siteId,
    landmark_id: landmarkId,
  });
}
