import os
import json
import cv2
import numpy as np
import torch
from transformers import AutoModelForDepthEstimation
from core.config import AppConfig

# Constantes de normalización ImageNet
IMAGE_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGE_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

class DepthEstimator:
    """
    Módulo para estimación métrica de profundidad usando Depth Anything V2.
    Soporta aceleración por CPU/CUDA, calibración lineal empírica y visualización.
    """

    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.config.apply_torch_settings()
        self.device = torch.device(self.config.device)
        
        print(f"[DepthEstimator] Cargando modelo: {self.config.depth_model_name} en dispositivo: {self.device}")
        self.model = AutoModelForDepthEstimation.from_pretrained(
            self.config.depth_model_name
        ).to(self.device).eval()
        
        # Cargar calibración por defecto
        self.a, self.b = self.load_calibration(self.config.calibration_file)

    @staticmethod
    def crop_bars(frame: np.ndarray, threshold: float = 8.0) -> np.ndarray:
        """
        Elimina barras negras (letterboxing) horizontales superiores e inferiores.
        """
        gray_mean = frame.mean(axis=(1, 2))
        rows = np.where(gray_mean > threshold)[0]
        if len(rows) == 0:
            return frame
        return frame[rows[0]:rows[-1] + 1]

    def estimate_raw(self, frame: np.ndarray) -> np.ndarray:
        """
        Estima la profundidad en metros 'crudos' (sin ajustar por calibración).
        Devuelve una matriz de profundidad con la misma resolución que el frame original.
        """
        h_orig, w_orig = frame.shape[:2]
        
        # Redimensionar a múltiplos de 14 para la arquitectura ViT
        img_resized = cv2.resize(frame, (self.config.depth_width, self.config.depth_height))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img_norm = (img_rgb - IMAGE_MEAN) / IMAGE_STD
        
        # Tensor CHW con dimensión de lote
        tensor = torch.from_numpy(img_norm.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(pixel_values=tensor)
            # Extraer tensor predicho y pasar a NumPy
            predicted_depth = outputs.predicted_depth[0]
            if predicted_depth.is_cuda:
                depth_np = predicted_depth.cpu().numpy()
            else:
                depth_np = predicted_depth.numpy()

        # Reescalar al tamaño del frame de entrada
        return cv2.resize(depth_np, (w_orig, h_orig))

    def estimate_calibrated(self, frame: np.ndarray) -> np.ndarray:
        """
        Estima la profundidad y aplica el factor de corrección lineal:
        dist_real ≈ a * dist_cruda + b
        """
        raw_depth = self.estimate_raw(frame)
        calibrated = self.a * raw_depth + self.b
        return np.clip(calibrated, 0.05, None)

    def load_calibration(self, file_path: str = None) -> tuple[float, float]:
        """
        Carga los parámetros de calibración 'a' (pendiente) y 'b' (intercepto) desde un JSON.
        """
        path = file_path or self.config.calibration_file
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.a = float(data.get("a", 1.0))
                self.b = float(data.get("b", 0.0))
                print(f"[DepthEstimator] Calibración cargada desde '{path}': a={self.a:.3f}, b={self.b:.3f}")
                return self.a, self.b
            except Exception as e:
                print(f"[DepthEstimator] Error leyendo calibración: {e}. Usando valores por defecto.")
        else:
            print(f"[DepthEstimator] No se encontró '{path}'. Usando escala sin calibrar (a=1.0, b=0.0).")
        
        self.a, self.b = 1.0, 0.0
        return self.a, self.b

    def save_calibration(self, a: float, b: float, points: list, file_path: str = None) -> str:
        """
        Guarda los parámetros calculados y los puntos de calibración en un JSON.
        """
        path = file_path or self.config.calibration_file
        self.a = float(a)
        self.b = float(b)
        data = {
            "a": self.a,
            "b": self.b,
            "formula": f"dist_real = {self.a:.4f} * valor_modelo + {self.b:.4f}",
            "puntos": points
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[DepthEstimator] Calibración guardada exitosamente en '{path}'")
        return path

    def colorize(self, depth_map: np.ndarray, max_meters: float = None) -> np.ndarray:
        """
        Genera un mapa de calor visual a partir de la matriz de profundidad.
        Colores TURBO: Azul = Cerca, Verde/Amarillo = Medio, Rojo = Lejos.
        """
        max_m = max_meters or self.config.max_depth_colormap
        depth_norm = np.clip(depth_map / max_m, 0.0, 1.0)
        depth_8bit = (depth_norm * 255).astype(np.uint8)
        # Invertir para que lo cercano (0) mapee a colores fríos y lo lejano a cálidos
        colored_map = cv2.applyColorMap(255 - depth_8bit, cv2.COLORMAP_TURBO)
        return colored_map

