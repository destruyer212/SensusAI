"""Optional YOLO adapter. Gemini remains the semantic fallback.

Author and code owner: Carlos Jesus Ascarate Riega
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from settings import settings

try:  # Optional so the existing Gemini backend stays deployable on t4g.micro.
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:  # Optional until the first local YOLO test installs requirements-yolo.txt.
    from ultralytics import YOLO
except ImportError:  # pragma: no cover
    YOLO = None


class YoloDetector:
    def __init__(self) -> None:
        self._model: Any | None = None

    @property
    def available(self) -> bool:
        return bool(settings.yolo_enabled and YOLO and Path(settings.yolo_model_path).exists())

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.yolo_enabled,
            "available": self.available,
            "model": settings.yolo_model_path,
            "dependency_installed": YOLO is not None,
        }

    def detect(self, image_bytes: bytes) -> list[dict[str, Any]]:
        if not self.available:
            raise RuntimeError(
                "YOLO no esta disponible. Instala backend/requirements-yolo.txt, "
                "descarga el peso configurado y activa YOLO_ENABLED=true."
            )
        if self._model is None:
            self._model = YOLO(settings.yolo_model_path)
        if Image is None:
            raise RuntimeError("Pillow es necesario para el adaptador YOLO.")

        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        results = self._model.predict(
            source=image,
            imgsz=settings.yolo_image_size,
            conf=settings.yolo_confidence_threshold,
            max_det=settings.yolo_max_detections,
            verbose=False,
        )
        detections: list[dict[str, Any]] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            names = getattr(result, "names", {})
            if boxes is None:
                continue
            xyxyn = boxes.xyxyn.cpu().tolist()
            confidences = boxes.conf.cpu().tolist()
            classes = boxes.cls.cpu().tolist()
            for bbox, confidence, class_id in zip(xyxyn, confidences, classes):
                detections.append(
                    {
                        "label": names.get(int(class_id), str(int(class_id))),
                        "confidence": float(confidence),
                        "bbox": [float(value) for value in bbox],
                    }
                )
        return detections


yolo_detector = YoloDetector()
