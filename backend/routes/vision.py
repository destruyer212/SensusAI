from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile, status
from starlette.concurrency import run_in_threadpool

from services.vision_ai import analyze_scene
from services.safety_governor import governor
from services.yolo_detector import yolo_detector
from services.depth_estimator import depth_estimator
from services.vision_pipeline import realtime_analyze, realtime_analyze_rgb_frame
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

    # Si Gemini esta apagado pero YOLO esta disponible, usar el pipeline YOLO + Depth
    if not settings.gemini_enabled and yolo_detector.available:
        return await run_in_threadpool(realtime_analyze, image_bytes)

    return await analyze_scene(image_bytes=image_bytes, mime_type=image.content_type, task=task or task_query)


@router.get("/capabilities")
async def capabilities() -> dict:
    """Expose active engines so the mobile client never guesses."""
    return {
        "gemini": {"enabled": settings.gemini_enabled, "model": settings.gemini_model},
        "yolo": yolo_detector.status(),
        "depth": depth_estimator.status(),
        "pipeline": "yolo_then_gemini_fallback",
    }


@router.post("/realtime")
async def realtime(
    image: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    session_query: str | None = Query(default=None, alias="session_id"),
) -> dict:
    """Hybrid realtime path: YOLO first, optional depth, never Gemini per frame."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="El archivo debe ser una imagen.")
    image_bytes = await image.read()
    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="La imagen es demasiado pesada.")
    try:
        return await run_in_threadpool(
            realtime_analyze,
            image_bytes,
            session_id=session_id or session_query or "default",
        )
    except RuntimeError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


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


@router.post("/realtime-frame")
async def realtime_frame(
    request: Request,
    width: int = Query(..., ge=1, le=1920),
    height: int = Query(..., ge=1, le=1920),
    bytes_per_row: int = Query(..., ge=1, le=16384),
    session_id: str | None = Query(default=None),
) -> dict:
    """Run YOLO on a native VisionCamera RGB frame buffer.

    This endpoint deliberately accepts application/octet-stream instead of a
    multipart photo. The phone keeps its camera stream active and sends only
    the sampled frame buffer needed by the realtime detector.
    """
    frame_bytes = await request.body()
    expected_max = bytes_per_row * height
    if len(frame_bytes) == 0 or len(frame_bytes) > expected_max:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Buffer de frame invalido.")
    try:
        return await run_in_threadpool(
            realtime_analyze_rgb_frame,
            frame_bytes,
            width=width,
            height=height,
            bytes_per_row=bytes_per_row,
            session_id=session_id or "default",
        )
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
