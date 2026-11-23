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
            left, right = sorted((int(x1 * width), int(x2 * width)))
            top, bottom = sorted((int(y1 * height), int(y2 * height)))
            region = depth[max(0, top):min(height, bottom), max(0, left):min(width, right)]
            item = dict(detection)
            raw_distance = float(np.percentile(region, 25)) if region.size else None
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
        y1, y2 = int(height * 0.25), int(height * 0.95)
        x1, x2 = int(width * 0.25), int(width * 0.75)
        corridor = depth[y1:y2, x1:x2]
        if not corridor.size:
            return None
        raw_distance = float(np.percentile(corridor, 20))
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
        
        Analiza el perfil vertical de profundidad en el corredor del suelo frente
        a los pies del usuario (y: 55% a 95%). Si hay un salto discontinuo positivo
        en la distancia (la superficie del piso 'cae' abruptamente), se genera una alerta.
        """
        depth = depth if depth is not None else self.estimate(image_bytes)
        height, width = depth.shape[:2]

        # Pasillo de pisada: tercio inferior central donde el usuario da sus proximos pasos
        y1, y2 = int(height * 0.55), int(height * 0.95)
        x1, x2 = int(width * 0.30), int(width * 0.70)
        floor_region = depth[y1:y2, x1:x2]
        if not floor_region.size:
            return None

        # Convertir a metros calibrados
        floor_m = np.clip(self.a * floor_region + self.b, 0.05, 10.0)

        # Perfil vertical del suelo (mediana por fila a lo largo del ancho del pasillo)
        # La fila 0 corresponde a y1 (mas lejos), la ultima a y2 (cerca de los pies)
        profile = np.median(floor_m, axis=1)

        step = max(3, len(profile) // 12)
        if len(profile) <= step:
            return None

        # diffs: incremento de distancia al avanzar hacia adelante (de abajo hacia arriba)
        # profile[:-step] (mas lejos) - profile[step:] (mas cerca)
        diffs = profile[:-step] - profile[step:]

        max_idx = int(np.argmax(diffs))
        max_jump = float(diffs[max_idx])

        # Umbral: un salto brusco mayor a 35 cm en el plano del suelo indica un desnivel
        DROP_THRESHOLD_M = 0.35
        if max_jump >= DROP_THRESHOLD_M:
            edge_row = y1 + max_idx + step
            distance_to_edge = float(profile[max_idx + step])

            # Alertar si el desnivel esta dentro del rango critico de pisada (< 2.4 m)
            if distance_to_edge < 2.4:
                confidence = round(min(1.0, max_jump / 0.6), 2)
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
                    "zone": "cuidado" if distance_to_edge < 1.2 else "atención",
                    "is_negative_obstacle": True,
                    "drop_height_m": round(max_jump, 2),
                }

        return None


depth_estimator = DepthEstimator()
