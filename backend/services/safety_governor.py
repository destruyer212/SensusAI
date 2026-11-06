"""Decision layer for short, temporal and conservative accessibility alerts.

Author and code owner: Carlos Jesus Ascarate Riega

This module intentionally does not claim that a 2D camera can measure exact
distance. It only estimates urgency from position, box size and change over
time. A real deployment must validate it with supervised users.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


RISK_ORDER = {"clear": 0, "notice": 1, "caution": 2, "danger": 3, "unknown": 1}


@dataclass
class SessionState:
    previous_area_by_label: dict[str, float] = field(default_factory=dict)
    last_spoken_by_key: dict[str, float] = field(default_factory=dict)
    last_risk: str = "clear"


class SafetyGovernor:
    """Turns raw detections into one prioritized response per frame."""

    def __init__(self, repeat_seconds: float = 3.0) -> None:
        self.repeat_seconds = repeat_seconds
        self.sessions: dict[str, SessionState] = defaultdict(SessionState)

    def evaluate(
        self,
        detections: list[dict[str, Any]],
        *,
        session_id: str = "default",
        now: float | None = None,
    ) -> dict[str, Any]:
        now = now if now is not None else time.monotonic()
        state = self.sessions[session_id]
        normalized: list[dict[str, Any]] = []

        for detection in detections:
            item = self._normalize(detection)
            label = item["label"]
            previous_area = state.previous_area_by_label.get(label, item["area"])
            item["growth"] = max(0.0, item["area"] - previous_area)
            state.previous_area_by_label[label] = item["area"]
            item["risk_level"] = self._risk_for(item)
            normalized.append(item)

        normalized.sort(key=lambda item: (RISK_ORDER[item["risk_level"]], item["confidence"], item["area"]), reverse=True)
        top = normalized[0] if normalized else None
        risk = top["risk_level"] if top else "clear"

        # Hysteresis: do not immediately announce "clear" after an urgent frame.
        if risk == "clear" and state.last_risk == "danger":
            risk = "caution"
        state.last_risk = risk

        text = self._message(top, risk)
        message_key = f"{risk}:{top['label'] if top else 'clear'}"
        urgent = risk == "danger"
        last_spoken = state.last_spoken_by_key.get(message_key, float("-inf"))
        should_speak = bool(text) and (urgent or now - last_spoken >= self.repeat_seconds)
        if should_speak:
            state.last_spoken_by_key[message_key] = now

        return {
            "mode": "yolo",
            "text": text,
            "speech": text,
            "risk_level": risk,
            "action": "stop" if risk == "danger" else "caution" if risk == "caution" else "observe",
            "should_speak": should_speak,
            "detections": normalized,
            "session_id": session_id,
            "note": "Distancia aproximada por visión 2D; confirmar antes de una acción crítica.",
        }

    @staticmethod
    def _normalize(detection: dict[str, Any]) -> dict[str, Any]:
        label = str(detection.get("label") or "objeto").lower()
        confidence = max(0.0, min(1.0, float(detection.get("confidence", 0.0))))
        bbox = detection.get("bbox") or [0.0, 0.0, 0.0, 0.0]
        x1, y1, x2, y2 = [float(value) for value in bbox]
        # YOLO adapter returns normalized coordinates. Pixel boxes are handled
        # by the adapter before reaching this layer.
        width = max(0.0, x2 - x1)
        height = max(0.0, y2 - y1)
        area = min(1.0, width * height)
        center_x = (x1 + x2) / 2
        bottom = y2
        position = "izquierda" if center_x < 0.35 else "derecha" if center_x > 0.65 else "al frente"
        return {
            "label": label,
            "confidence": round(confidence, 3),
            "bbox": [round(x1, 4), round(y1, 4), round(x2, 4), round(y2, 4)],
            "area": round(area, 4),
            "position": position,
            "bottom": round(bottom, 4),
        }

    @staticmethod
    def _risk_for(item: dict[str, Any]) -> str:
        confidence = item["confidence"]
        area = item["area"]
        bottom = item["bottom"]
        growth = item["growth"]
        if confidence < 0.35:
            return "unknown"
        # A large, central, low-in-frame object or a rapidly growing box is the
        # strongest visual proxy for an imminent collision.
        if (area >= 0.20 and bottom >= 0.72 and confidence >= 0.58) or (growth >= 0.12 and bottom >= 0.62):
            return "danger"
        if (area >= 0.07 and bottom >= 0.58) or (growth >= 0.05 and bottom >= 0.50):
            return "caution"
        return "notice"

    @staticmethod
    def _message(top: dict[str, Any] | None, risk: str) -> str:
        if not top:
            return ""
        if risk == "danger":
            return f"Detente. {top['label']} muy cerca {top['position']}."
        if risk == "caution":
            return f"Cuidado: {top['label']} {top['position']}."
        if risk == "notice":
            return f"Detectado: {top['label']} {top['position']}."
        return "No estoy seguro de lo que detecto. Avanza con precaucion."


governor = SafetyGovernor()
