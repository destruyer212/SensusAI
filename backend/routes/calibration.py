"""Endpoints para calibración métrica del estimador de profundidad.

Flujo de calibración:
1. GET  /api/calibration/status        → lee a, b actuales y puntos guardados
2. POST /api/calibration/sample        → recibe foto JPEG (base64), devuelve la
                                         profundidad cruda del centro de la imagen
3. POST /api/calibration/point         → registra un par (raw_depth, real_m) en sesión
4. POST /api/calibration/save          → calcula regresión lineal y guarda calibracion.json
5. DELETE /api/calibration/points      → limpia la sesión sin guardar
6. POST /api/calibration/reset         → vuelve a a=1.0, b=0.0 (sin calibración)
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.depth_estimator import depth_estimator
from settings import ROOT_DIR, settings

logger = logging.getLogger("sensus.calibration")
router = APIRouter(tags=["calibration"])

# Almacén en memoria de puntos (raw_depth, real_m) recolectados en la sesión actual.
# Se limpia al guardar o al hacer reset.
_session_points: list[tuple[float, float]] = []


# ---------------------------------------------------------------------------
# Modelos de entrada
# ---------------------------------------------------------------------------

class SamplePayload(BaseModel):
    """Imagen JPEG codificada en base64 para medir la profundidad central."""
    image_b64: str = Field(..., description="JPEG completo en base64")


class PointPayload(BaseModel):
    """Par de valores a registrar en la sesión de calibración."""
    raw_depth: float = Field(..., description="Valor crudo devuelto por /calibration/sample")
    real_m: float = Field(..., gt=0, description="Distancia real medida en metros")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calibration_path() -> Path:
    path = Path(settings.depth_calibration_file)
    return path if path.is_absolute() else ROOT_DIR / path


def _read_calibration_file() -> dict[str, Any]:
    try:
        return json.loads(_calibration_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_calibration_file(a: float, b: float, points: list[tuple[float, float]], nota: str = "") -> Path:
    data: dict[str, Any] = {
        "a": a,
        "b": b,
        "formula": f"dist_real = {a:.4f} * valor_modelo + {b:.4f}",
        "puntos": [{"modelo": r, "real": m} for r, m in points],
    }
    if nota:
        data["nota"] = nota
    path = _calibration_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/calibration/status")
def calibration_status() -> dict[str, Any]:
    """Devuelve el estado actual de la calibración y los puntos de la sesión."""
    data = _read_calibration_file()
    a = float(data.get("a", 1.0))
    b = float(data.get("b", 0.0))
    return {
        "a": a,
        "b": b,
        "formula": data.get("formula", f"dist_real = {a:.4f} * valor_modelo + {b:.4f}"),
        "calibrated": not (abs(a - 1.0) < 1e-6 and abs(b) < 1e-6),
        "points_saved": len(data.get("puntos", [])),
        "points_session": len(_session_points),
        "session_points": [
            {"raw": round(r, 4), "real": round(m, 3)}
            for r, m in _session_points
        ],
        "depth_available": depth_estimator.available,
    }


@router.post("/calibration/sample")
async def take_sample(payload: SamplePayload) -> dict[str, Any]:
    """Recibe una imagen JPEG en base64 y devuelve la profundidad cruda del centro.

    El cliente debe:
    1. Tomar una foto con la cámara.
    2. Codificarla en base64.
    3. Llamar a este endpoint.
    4. Medir físicamente la distancia al objeto central.
    5. Enviar ambos valores a POST /api/calibration/point.
    """
    if not depth_estimator.available:
        raise HTTPException(
            status_code=503,
            detail="El estimador de profundidad no está disponible en este servidor.",
        )

    try:
        image_bytes = base64.b64decode(payload.image_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Imagen base64 inválida.")

    try:
        depth_map = depth_estimator.estimate(image_bytes)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error al estimar profundidad: {err}")

    # Muestrear la región central (10% del lado menor centrado)
    h, w = depth_map.shape[:2]
    half = max(5, min(h, w) // 10)
    cy, cx = h // 2, w // 2
    region = depth_map[max(0, cy - half):cy + half, max(0, cx - half):cx + half]
    raw_depth = float(np.median(region)) if region.size > 0 else 0.0

    logger.info("[Calibración] Muestra tomada: raw_depth=%.4f (sesión: %d puntos)", raw_depth, len(_session_points))

    return {
        "raw_depth": round(raw_depth, 4),
        "points_session": len(_session_points),
        "hint": "Mide la distancia real al objeto central y llama a POST /api/calibration/point",
    }


@router.post("/calibration/point")
def add_calibration_point(payload: PointPayload) -> dict[str, Any]:
    """Agrega un par (raw_depth, real_m) a la sesión de calibración."""
    _session_points.append((payload.raw_depth, payload.real_m))
    logger.info(
        "[Calibración] Punto agregado #%d: modelo=%.4f, real=%.3f m",
        len(_session_points), payload.raw_depth, payload.real_m,
    )
    return {
        "ok": True,
        "points_session": len(_session_points),
        "points": [
            {"raw": round(r, 4), "real": round(m, 3)}
            for r, m in _session_points
        ],
        "ready_to_save": len(_session_points) >= 2,
    }


@router.delete("/calibration/points")
def clear_session_points() -> dict[str, Any]:
    """Elimina todos los puntos de la sesión actual sin modificar calibracion.json."""
    _session_points.clear()
    logger.info("[Calibración] Sesión limpiada.")
    return {"ok": True, "points_session": 0}


@router.post("/calibration/save")
def save_calibration() -> dict[str, Any]:
    """Calcula la regresión lineal con los puntos de la sesión y guarda calibracion.json.

    Fórmula ajustada: dist_real = a * raw_depth + b
    Se necesitan al menos 2 puntos con distancias reales distintas.
    """
    if len(_session_points) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Se necesitan al menos 2 puntos de calibración. "
                f"Actualmente hay {len(_session_points)}."
            ),
        )

    xs = np.array([p[0] for p in _session_points])
    ys = np.array([p[1] for p in _session_points])

    if np.allclose(xs, xs[0]):
        raise HTTPException(
            status_code=400,
            detail="Todos los puntos tienen el mismo valor de modelo. Usa distancias distintas.",
        )

    a, b = np.polyfit(xs, ys, 1)
    a, b = float(a), float(b)

    saved_points = list(_session_points)
    path = _write_calibration_file(a, b, saved_points)

    # Aplicar inmediatamente al estimador en memoria (sin reiniciar el servidor)
    depth_estimator.a = a
    depth_estimator.b = b

    _session_points.clear()

    logger.info("[Calibración] Guardada: a=%.4f, b=%.4f en %s", a, b, path)

    # Calcular error promedio para feedback
    errors = [abs((a * x + b) - y) for x, y in saved_points]
    mae = float(np.mean(errors))

    return {
        "ok": True,
        "a": round(a, 4),
        "b": round(b, 4),
        "formula": f"dist_real = {a:.4f} * valor_modelo + {b:.4f}",
        "points_used": len(saved_points),
        "mae_m": round(mae, 3),
        "file": str(path),
        "points_detail": [
            {
                "raw": round(x, 4),
                "real": round(y, 3),
                "ajustado": round(a * x + b, 3),
                "error": round(abs((a * x + b) - y), 3),
            }
            for x, y in saved_points
        ],
    }


@router.post("/calibration/reset")
def reset_calibration() -> dict[str, Any]:
    """Restablece la calibración a a=1.0, b=0.0 (sin corrección)."""
    _session_points.clear()
    path = _write_calibration_file(
        1.0, 0.0, [],
        nota="Calibración neutra. Usa la app para calibrar con tu cámara.",
    )
    depth_estimator.a = 1.0
    depth_estimator.b = 0.0
    logger.info("[Calibración] Restablecida a valores neutros.")
    return {"ok": True, "a": 1.0, "b": 0.0, "file": str(path)}
