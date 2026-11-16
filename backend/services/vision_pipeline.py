"""Single hybrid entry point for realtime vision."""

from __future__ import annotations

from typing import Any

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
            has_front_risk = any(
                item.get("position") == "al frente"
                and item.get("distance_m") is not None
                and item["distance_m"] < 2.5
                for item in detections
            )
            if front_obstacle and not has_front_risk:
                detections.append(front_obstacle)
            depth_used = True
        except Exception as error:  # depth must never take down YOLO alerts
            print(f"[vision_pipeline] profundidad no disponible: {error}")

    response = governor.evaluate(detections, session_id=session_id)
    response["mode"] = "hybrid" if depth_used else "yolo"
    response["engines"] = {"yolo": True, "depth": depth_used, "gemini": False}
    return response
