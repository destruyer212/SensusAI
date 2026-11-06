from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.vision import router as vision_router
from routes.spatial import router as spatial_router
from routes.command import router as command_router
from settings import settings
from services.yolo_detector import yolo_detector


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend API de Sensus AI para inteligencia espacial asistida.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(vision_router, prefix="/api")
    app.include_router(spatial_router, prefix="/api")
    app.include_router(command_router, prefix="/api")

    @app.get("/", tags=["system"])
    def root() -> dict:
        return {
            "app": settings.app_name,
            "type": "backend-api",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["system"])
    def health() -> dict:
        return {
            "ok": True,
            "app": settings.app_name,
            "gemini_enabled": settings.gemini_enabled,
            "yolo_enabled": settings.yolo_enabled,
            "yolo_available": yolo_detector.available,
        }

    return app


app = create_app()


if __name__ == "__main__":
    from pathlib import Path

    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        app_dir=str(Path(__file__).parent),
    )
