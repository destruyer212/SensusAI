from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status

from services.spatial_core import (
    get_emergency_guidance,
    get_route,
    list_destinations,
    list_sites,
    resolve_qr,
)


router = APIRouter(prefix="/spatial", tags=["spatial"])


class QrPayload(BaseModel):
    qr_code: str


class RoutePayload(BaseModel):
    site_id: str
    from_landmark_id: str
    destination_id: str


class EmergencyPayload(BaseModel):
    site_id: str
    from_landmark_id: str | None = None


@router.get("/sites")
def sites() -> dict:
    return {"sites": list_sites()}


@router.post("/qr")
def qr_lookup(payload: QrPayload) -> dict:
    result = resolve_qr(payload.qr_code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR no registrado en Spatial Core.",
        )
    return result


@router.get("/sites/{site_id}/destinations")
def destinations(site_id: str) -> dict:
    result = list_destinations(site_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lugar no encontrado.",
        )
    return {"destinations": result}


@router.post("/route")
def route(payload: RoutePayload) -> dict:
    result = get_route(
        site_id=payload.site_id,
        from_landmark_id=payload.from_landmark_id,
        destination_id=payload.destination_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruta no encontrada en Spatial Core.",
        )
    return result


@router.post("/emergency")
def emergency(payload: EmergencyPayload) -> dict:
    result = get_emergency_guidance(
        site_id=payload.site_id,
        from_landmark_id=payload.from_landmark_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guia de emergencia no encontrada.",
        )
    return result
