import Constants from "expo-constants";
const configuredUrl = Constants.expoConfig?.extra?.apiBaseUrl;
const API_BASE_URL = configuredUrl || "http://localhost:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function analyzeScene(imageUri, task = "navigation") {
  const formData = new FormData();
  formData.append("image", {
    uri: imageUri,
    name: "scene.jpg",
    type: "image/jpeg",
  });
  formData.append("task", task);

  const response = await fetch(`${API_BASE_URL}/api/vision/analyze`, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Sensus API error: ${response.status} ${detail}`);
  }

  return response.json();
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
