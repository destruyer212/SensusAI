"""Single hybrid entry point for realtime vision."""

from __future__ import annotations

from typing import Any
from io import BytesIO

from PIL import Image

from services.depth_estimator import depth_estimator
from services.safety_governor import governor
from services.yolo_detector import yolo_detector


def realtime_analyze(image_bytes: bytes, *, session_id: str = "default") -> dict[str, Any]:
    if not yolo_detector.available:
        raise RuntimeError("YOLO no esta disponible para el modo realtime.")

    detections = yolo_detector.detect(image_bytes)
    depth_used = False
    if depth_estimator.available:
        try:
            depth_map = depth_estimator.estimate(image_bytes)
            detections = depth_estimator.enrich(image_bytes, detections, depth=depth_map)
            front_obstacle = depth_estimator.central_obstacle(image_bytes, depth=depth_map)
            dropoff = depth_estimator.detect_dropoff(image_bytes, depth=depth_map)
            has_front_risk = any(
                item.get("position") == "al frente"
                and item.get("distance_m") is not None
                and item["distance_m"] < 2.5
                for item in detections
            )
            if front_obstacle and not has_front_risk:
                detections.append(front_obstacle)
            if dropoff:
                detections.append(dropoff)
            depth_used = True
        except Exception as error:  # depth must never take down YOLO alerts
            print(f"[vision_pipeline] profundidad no disponible: {error}")

    response = governor.evaluate(detections, session_id=session_id)
    response["mode"] = "hybrid" if depth_used else "yolo"
    response["engines"] = {"yolo": True, "depth": depth_used, "gemini": False}
    return response


def realtime_analyze_rgb_frame(
    frame_bytes: bytes,
    *,
    width: int,
    height: int,
    bytes_per_row: int,
    session_id: str = "default",
) -> dict[str, Any]:
    """Convert one native VisionCamera RGB frame and run the realtime pipeline.

    The mobile app sends a sampled frame buffer, not a captured photo. Keeping
    the conversion here makes the transport explicit and leaves YOLO/depth in
    the same tested pipeline used by the existing JPEG endpoint.
    """
    if width <= 0 or height <= 0 or width > 1920 or height > 1920:
        raise ValueError("Dimensiones de frame invalidas.")

    pixels = width * height
    if len(frame_bytes) >= pixels * 4 and bytes_per_row >= width * 4:
        rgba = bytearray(pixels * 4)
        for row in range(height):
            source_start = row * bytes_per_row
            target_start = row * width * 4
            rgba[target_start : target_start + width * 4] = frame_bytes[source_start : source_start + width * 4]
        image = Image.frombytes("RGBA", (width, height), bytes(rgba)).convert("RGB")
    elif len(frame_bytes) >= pixels * 3 and bytes_per_row >= width * 3:
        rgb = bytearray(pixels * 3)
        for row in range(height):
            source_start = row * bytes_per_row
            target_start = row * width * 3
            rgb[target_start : target_start + width * 3] = frame_bytes[source_start : source_start + width * 3]
        image = Image.frombytes("RGB", (width, height), bytes(rgb))
    else:
        raise ValueError("El buffer RGB del frame esta incompleto.")

    encoded = BytesIO()
    image.save(encoded, format="JPEG", quality=68, optimize=False)
    return realtime_analyze(encoded.getvalue(), session_id=session_id)
