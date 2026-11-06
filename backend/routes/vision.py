from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from starlette.concurrency import run_in_threadpool

from services.vision_ai import analyze_scene
from services.safety_governor import governor
from services.yolo_detector import yolo_detector
from settings import settings


router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    task: str | None = Form(default=None),
    task_query: str | None = Query(default=None, alias="task"),
) -> dict:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="El archivo debe ser una imagen.",
        )

    image_bytes = await image.read()
    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La imagen es demasiado pesada.",
        )

    return await analyze_scene(image_bytes=image_bytes, mime_type=image.content_type, task=task or task_query)


@router.get("/capabilities")
async def capabilities() -> dict:
    """Expose active engines so the mobile client never guesses."""
    return {
        "gemini": {"enabled": settings.gemini_enabled, "model": settings.gemini_model},
        "yolo": yolo_detector.status(),
        "pipeline": "yolo_then_gemini_fallback",
    }


@router.post("/fast-detect")
async def fast_detect(
    image: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    session_query: str | None = Query(default=None, alias="session_id"),
) -> dict:
    """Fast path: YOLO + temporal safety logic; no Gemini token is spent."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="El archivo debe ser una imagen.")
    image_bytes = await image.read()
    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen es demasiado pesada.")
    if not yolo_detector.available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=yolo_detector.status())
    try:
        detections = await run_in_threadpool(yolo_detector.detect, image_bytes)
        return governor.evaluate(detections, session_id=session_id or session_query or "default")
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
