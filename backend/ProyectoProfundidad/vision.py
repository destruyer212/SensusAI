"""
Módulo de compatibilidad hacia atrás para estimación de profundidad.
Delega internamente en la arquitectura centralizada 'core.depth.DepthEstimator'.
"""
from typing import Tuple
import numpy as np
from core.config import AppConfig
from core.depth import DepthEstimator

# Instancia singleton predeterminada
_default_config = AppConfig()
_estimator: DepthEstimator = None

def _get_estimator() -> DepthEstimator:
    global _estimator
    if _estimator is None:
        _estimator = DepthEstimator(_default_config)
    return _estimator

def recortar_barras(frame: np.ndarray) -> np.ndarray:
    """Elimina las barras negras de letterboxing."""
    return DepthEstimator.crop_bars(frame)

def estimar_profundidad(frame: np.ndarray) -> np.ndarray:
    """Estima metros métricos 'crudos' del modelo Depth Anything V2."""
    return _get_estimator().estimate_raw(frame)

def cargar_calibracion(ruta: str = "calibracion.json") -> Tuple[float, float]:
    """Carga los coeficientes 'a' y 'b' de calibración lineal."""
    return _get_estimator().load_calibration(ruta)

def profundidad_calibrada(frame: np.ndarray, a: float = None, b: float = None) -> np.ndarray:
    """Calcula la profundidad aplicando la calibración (a * d + b)."""
    est = _get_estimator()
    if a is not None and b is not None:
        raw = est.estimate_raw(frame)
        return np.clip(a * raw + b, 0.05, None)
    return est.estimate_calibrated(frame)

if __name__ == "__main__":
    print("[vision.py] Probando módulo de visión centralizado...")
    est = _get_estimator()
    print(f"Dispositivo activo: {est.device}, Calibración: a={est.a}, b={est.b}")
