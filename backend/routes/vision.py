from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from services.vision_ai import analyze_scene
from settings import settings


router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/analyze")
async def analyze(image: UploadFile = File(...), task: str | None = Form(default=None)) -> dict:
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

    return await analyze_scene(image_bytes=image_bytes, mime_type=image.content_type, task=task)
