"""Optional monocular depth adapter for the SensusAI realtime pipeline.

Depth is deliberately optional: Gemini and YOLO must keep working when the
large Hugging Face model is not installed. Distances are estimates and require
camera calibration before being used for safety-critical decisions.
"""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from typing import Any

import numpy as np

from settings import ROOT_DIR, settings

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation
except ImportError:  # pragma: no cover
    torch = None
    AutoImageProcessor = None
    AutoModelForDepthEstimation = None


class DepthEstimator:
    def __init__(self) -> None:
        self._processor: Any | None = None
        self._model: Any | None = None
        self._device = "cuda" if torch is not None and torch.cuda.is_available() else "cpu"
        self.a, self.b = self._load_calibration()

    def _load_calibration(self) -> tuple[float, float]:
        path = Path(settings.depth_calibration_file)
        if not path.is_absolute():
            path = ROOT_DIR / path
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return float(data.get("a", settings.depth_calibration_a)), float(data.get("b", settings.depth_calibration_b))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return settings.depth_calibration_a, settings.depth_calibration_b

    @property
    def available(self) -> bool:
        return bool(
            settings.depth_enabled
            and Image is not None
            and torch is not None
            and AutoImageProcessor is not None
            and AutoModelForDepthEstimation is not None
        )

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.depth_enabled,
            "available": self.available,
            "model": settings.depth_model_name,
            "dependency_installed": AutoModelForDepthEstimation is not None,
            "device": self._device,
            "note": "Distancia monocular aproximada; calibrar antes de uso real.",
        }

    def _load(self) -> None:
        if self._model is not None:
            return
        if not self.available:
            raise RuntimeError("Profundidad no disponible. Activa DEPTH_ENABLED e instala requirements-vision.txt.")
        self._processor = AutoImageProcessor.from_pretrained(settings.depth_model_name)
        self._model = AutoModelForDepthEstimation.from_pretrained(settings.depth_model_name).to(self._device).eval()

    def estimate(self, image_bytes: bytes) -> np.ndarray:
        self._load()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {key: value.to(self._device) for key, value in inputs.items()}
        with torch.no_grad():
            prediction = self._model(**inputs).predicted_depth
        depth = prediction.squeeze().detach().float().cpu().numpy()
        return depth

    def enrich(self, image_bytes: bytes, detections: list[dict[str, Any]], depth: np.ndarray | None = None) -> list[dict[str, Any]]:
        depth = depth if depth is not None else self.estimate(image_bytes)
        height, width = depth.shape[:2]
        enriched: list[dict[str, Any]] = []
        for detection in detections[: settings.depth_max_objects]:
            bbox = detection.get("bbox") or [0, 0, 0, 0]
            x1, y1, x2, y2 = [max(0.0, min(1.0, float(value))) for value in bbox]
            
            # Para evitar que el fondo, la mesa o el suelo alrededor contaminen
            # la distancia del objeto, recortamos los margenes un 15% hacia el centro (core).
            w_box = max(0.01, x2 - x1)
            h_box = max(0.01, y2 - y1)
            cx1 = max(0.0, x1 + 0.15 * w_box)
            cx2 = min(1.0, x2 - 0.15 * w_box)
            cy1 = max(0.0, y1 + 0.15 * h_box)
            cy2 = min(1.0, y2 - 0.15 * h_box)

            left, right = sorted((int(cx1 * width), int(cx2 * width)))
            top, bottom = sorted((int(cy1 * height), int(cy2 * height)))
            region = depth[max(0, top):min(height, bottom), max(0, left):min(width, right)]

            # Fallback al bbox completo si la region central resulto vacia
            if not region.size:
                left, right = sorted((int(x1 * width), int(x2 * width)))
                top, bottom = sorted((int(y1 * height), int(y2 * height)))
                region = depth[max(0, top):min(height, bottom), max(0, left):min(width, right)]

            item = dict(detection)
            # Usar la mediana del nucleo central para maxima estabilidad frente a ruido
            raw_distance = float(np.median(region)) if region.size else None
            item["depth_score"] = round(raw_distance, 4) if raw_distance is not None else None
            item["distance_m"] = round(max(0.05, self.a * raw_distance + self.b), 2) if raw_distance is not None else None
            item["position"] = "izquierda" if (x1 + x2) / 2 < 0.35 else "derecha" if (x1 + x2) / 2 > 0.65 else "al frente"
            distance = item["distance_m"]
            item["zone"] = "cuidado" if distance is not None and distance < settings.depth_danger_m else "atención" if distance is not None and distance < settings.depth_attention_m else "seguro"
            enriched.append(item)
        return enriched

    def central_obstacle(self, image_bytes: bytes, depth: np.ndarray | None = None) -> dict[str, Any] | None:
        depth = depth if depth is not None else self.estimate(image_bytes)
        height, width = depth.shape[:2]
        # Corredor central enfocado (evita bordes laterales extremos y parte superior lejana)
        y1, y2 = int(height * 0.35), int(height * 0.85)
        x1, x2 = int(width * 0.35), int(width * 0.65)
        corridor = depth[y1:y2, x1:x2]
        if not corridor.size:
            return None
        # Mediana estable del pasillo central
        raw_distance = float(np.median(corridor))
        distance = max(0.05, self.a * raw_distance + self.b)
        if distance >= settings.depth_corridor_m:
            return None
        return {
            "label": "obstáculo al frente",
            "confidence": 1.0,
            "bbox": [0.25, 0.25, 0.75, 0.95],
            "distance_m": round(distance, 2),
            "position": "al frente",
            "zone": "cuidado" if distance < settings.depth_danger_m else "atención",
            "central_obstacle": True,
        }

    def detect_dropoff(self, image_bytes: bytes, depth: np.ndarray | None = None) -> dict[str, Any] | None:
        """Detecta obstaculos negativos: escalones hacia abajo, huecos o desniveles bruscos.

        Analiza el perfil de profundidad en el corredor del suelo frente al usuario
        (y: 60% a 95%). Para descartar falsos positivos causados por la silueta superior
        de objetos colocados en el suelo o sobre una mesa (obstaculos positivos),
        exige:
          1. Uniformidad horizontal (un escalon se extiende de lado a lado; un objeto
             es una protuberancia convexa en el centro).
          2. Continuidad plana del suelo antes del borde.
          3. Un salto discontinuo de al menos 45 cm que se mantiene hacia el fondo.
        """
        depth = depth if depth is not None else self.estimate(image_bytes)
        height, width = depth.shape[:2]

        # Pasillo de pisada: tercio inferior central donde el usuario pisa
        y1, y2 = int(height * 0.60), int(height * 0.95)
        x1, x2 = int(width * 0.25), int(width * 0.75)
        floor_region = depth[y1:y2, x1:x2]
        if not floor_region.size:
            return None

        # Convertir a metros calibrados
        floor_m = np.clip(self.a * floor_region + self.b, 0.05, 10.0)
        h_patch, w_patch = floor_m.shape[:2]

        # 1. Filtro de Convexidad Horizontal:
        # En un escalon/acera, la profundidad a lo largo de cada fila horizontal es pareja.
        # En un objeto puesto en el suelo o mesa (ej. juguete, caja, pelota), el centro
        # esta mucho mas cerca de la camara que los extremos de la misma fila.
        col_w = max(2, w_patch // 4)
        left_strip = np.median(floor_m[:, :col_w], axis=1)
        center_strip = np.median(floor_m[:, col_w : w_patch - col_w], axis=1)
        right_strip = np.median(floor_m[:, w_patch - col_w :], axis=1)

        # Si el centro sobresale hacia la camara mas de 12 cm respecto a los lados,
        # es un objeto positivo que resalta, NO suelo continuo
        protrusion = np.maximum(left_strip - center_strip, right_strip - center_strip)
        if float(np.mean(protrusion[-int(h_patch * 0.5):])) > 0.12:
            return None

        # 2. Perfil vertical continuo en el centro del pasillo
        profile = center_strip
        step = max(3, len(profile) // 10)
        if len(profile) <= step * 2:
            return None

        # diffs: salto de distancia hacia adelante (de fila inferior a superior)
        diffs = profile[:-step] - profile[step:]
        max_idx = int(np.argmax(diffs))
        max_jump = float(diffs[max_idx])

        # Umbral: se requiere un salto marcado de al menos 45 cm
        DROP_THRESHOLD_M = 0.45
        if max_jump >= DROP_THRESHOLD_M:
            edge_row = y1 + max_idx + step
            distance_to_edge = float(profile[max_idx + step])

            # 3. Comprobar que tras el salto la profundidad se mantenga profunda
            # (un escalon no es una linea fina, el nuevo nivel del suelo continua abajo)
            after_edge = profile[max(0, max_idx - step) : max_idx]
            if after_edge.size and float(np.median(after_edge)) < distance_to_edge + 0.25:
                return None

            # Alertar solo dentro del rango critico de paso (< 2.2 m)
            if distance_to_edge < 2.2:
                confidence = round(min(1.0, max_jump / 0.7), 2)
                return {
                    "label": "desnivel o escalón al frente",
                    "confidence": confidence,
                    "bbox": [
                        0.25,
                        round(max(0.0, (edge_row - step) / height), 4),
                        0.75,
                        round(min(1.0, (edge_row + step) / height), 4),
                    ],
                    "distance_m": round(distance_to_edge, 2),
                    "position": "al frente",
                    "zone": "cuidado" if distance_to_edge < 1.1 else "atención",
                    "is_negative_obstacle": True,
                    "drop_height_m": round(max_jump, 2),
                }

        return None


depth_estimator = DepthEstimator()
