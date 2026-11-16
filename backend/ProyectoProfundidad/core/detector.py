from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
import numpy as np
from ultralytics import YOLO
from core.config import AppConfig

@dataclass
class DetectionResult:
    class_id: int
    name_en: str
    name_es: str
    confidence: float
    box_xyxy: Tuple[int, int, int, int]
    center: Tuple[int, int]
    position: str            # 'al frente', 'a tu derecha', 'a tu izquierda'
    distance: Optional[float] # En metros
    zone: str                 # 'peligro', 'atencion', 'seguro'
    color: Tuple[int, int, int]

class ObjectDetector:
    """
    Detector de objetos 2D (YOLO) integrado con cálculo de distancia espacial
    y determinación de posición respecto al usuario.
    """

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        print(f"[ObjectDetector] Cargando modelo YOLO: {self.config.yolo_model_path}")
        self.model = YOLO(self.config.yolo_model_path)

    def get_horizontal_position(self, cx: float, width: float) -> str:
        """
        Determina la posición horizontal relativa al punto de vista del usuario.
        """
        if cx < width / 3.0:
            return "a tu derecha"
        if cx > 2.0 * width / 3.0:
            return "a tu izquierda"
        return "al frente"

    @staticmethod
    def compute_box_distance(depth_map: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> Optional[float]:
        """
        Calcula la distancia de un objeto usando la sub-región central del bounding box
        y el percentil 25 para capturar el punto más cercano del objeto sin ruido de fondo.
        """
        if depth_map is None:
            return None

        h = y2 - y1
        w = x2 - x1
        if h <= 4 or w <= 4:
            return None

        # Zona central: 50% interior del box
        crop_y1 = y1 + h // 4
        crop_y2 = y2 - h // 4
        crop_x1 = x1 + w // 4
        crop_x2 = x2 - w // 4

        region = depth_map[crop_y1:crop_y2, crop_x1:crop_x2]
        if region.size == 0:
            return None

        # Percentil 25 representa la superficie frontal del obstáculo
        return float(np.percentile(region, 25))

    def get_zone_and_color(self, distance: Optional[float]) -> Tuple[str, Tuple[int, int, int]]:
        """
        Clasifica la severidad del riesgo según la distancia métrica.
        """
        if distance is None:
            return "desconocido", (200, 200, 200)
        if distance < self.config.dist_peligro:
            return "cuidado", (0, 0, 255)       # Rojo
        if distance < self.config.dist_atencion:
            return "atención", (0, 200, 255)    # Ámbar / Naranja
        return "seguro", (0, 255, 0)            # Verde

    def detect(self, frame: np.ndarray, depth_map: Optional[np.ndarray] = None) -> List[DetectionResult]:
        """
        Ejecuta la inferencia YOLO y cruza los resultados con el mapa de profundidad.
        """
        h_frame, w_frame = frame.shape[:2]
        results = self.model(frame, conf=self.config.yolo_confidence, verbose=False)[0]

        detections: List[DetectionResult] = []
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name_en = results.names[cls_id]
            name_es = self.config.class_translations.get(name_en, name_en)

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            pos = self.get_horizontal_position(cx, w_frame)
            dist = self.compute_box_distance(depth_map, x1, y1, x2, y2)
            zone, color = self.get_zone_and_color(dist)

            detections.append(DetectionResult(
                class_id=cls_id,
                name_en=name_en,
                name_es=name_es,
                confidence=conf,
                box_xyxy=(x1, y1, x2, y2),
                center=(cx, cy),
                position=pos,
                distance=dist,
                zone=zone,
                color=color
            ))

        return detections

