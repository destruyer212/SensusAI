import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*")
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Sensus AI")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    gemini_timeout_seconds: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "7"))
    gemini_max_output_tokens: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "220"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(4 * 1024 * 1024)))
    yolo_enabled: bool = os.getenv("YOLO_ENABLED", "false").lower() == "true"
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "backend/models/yolo26n.pt")
    yolo_confidence_threshold: float = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.45"))
    yolo_image_size: int = int(os.getenv("YOLO_IMAGE_SIZE", "320"))
    yolo_max_detections: int = int(os.getenv("YOLO_MAX_DETECTIONS", "12"))
    depth_enabled: bool = os.getenv("DEPTH_ENABLED", "false").lower() == "true"
    depth_model_name: str = os.getenv(
        "DEPTH_MODEL_NAME",
        "depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf",
    )
    depth_image_size: int = int(os.getenv("DEPTH_IMAGE_SIZE", "336"))
    depth_max_objects: int = int(os.getenv("DEPTH_MAX_OBJECTS", "12"))
    depth_calibration_file: str = os.getenv("DEPTH_CALIBRATION_FILE", "backend/ProyectoProfundidad/calibracion.json")
    depth_calibration_a: float = float(os.getenv("DEPTH_CALIBRATION_A", "1.0"))
    depth_calibration_b: float = float(os.getenv("DEPTH_CALIBRATION_B", "0.0"))
    depth_danger_m: float = float(os.getenv("DEPTH_DANGER_M", "1.0"))
    depth_attention_m: float = float(os.getenv("DEPTH_ATTENTION_M", "2.5"))
    depth_corridor_m: float = float(os.getenv("DEPTH_CORRIDOR_M", "1.6"))
    safety_repeat_seconds: float = float(os.getenv("SAFETY_REPEAT_SECONDS", "3.0"))
    allowed_origins: list[str] = field(default_factory=_origins)

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
