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
    allowed_origins: list[str] = field(default_factory=_origins)

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
