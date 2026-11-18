from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from services.webrtc_service import webrtc_manager


router = APIRouter(prefix="/webrtc", tags=["webrtc"])


class OfferPayload(BaseModel):
    sdp: str = Field(..., description="SDP de oferta generado por el cliente WebRTC")
    type: str = Field(default="offer", description="Tipo de descripcion SDP (offer)")
    session_id: str = Field(default="mobile-default", description="Identificador de sesion del usuario")


class CandidatePayload(BaseModel):
    session_id: str = Field(default="mobile-default", description="Identificador de sesion")
    candidate: dict[str, Any] = Field(..., description="Objeto ICE candidate recibido del cliente")


@router.get("/status")
async def webrtc_status() -> dict[str, Any]:
    """Retorna si el soporte WebRTC (aiortc) esta disponible en el backend."""
    return {
        "available": webrtc_manager.available,
        "active_sessions": list(webrtc_manager.pcs.keys()),
    }


@router.post("/offer")
async def webrtc_offer(payload: OfferPayload) -> dict[str, str]:
    """Recibe la oferta WebRTC de video continuo del movil y responde con el SDP Answer."""
    if not webrtc_manager.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="aiortc no esta disponible en el servidor. Instala aiortc en requirements.txt.",
        )
    try:
        answer = await webrtc_manager.handle_offer(
            sdp=payload.sdp,
            sdp_type=payload.type,
            session_id=payload.session_id,
        )
        return answer
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al negociar conexion WebRTC: {error}",
        ) from error


@router.post("/candidate")
async def webrtc_candidate(payload: CandidatePayload) -> dict[str, bool]:
    """Endpoint opcional para recibir ICE candidates trickleados por el cliente."""
    success = await webrtc_manager.handle_ice_candidate(payload.session_id, payload.candidate)
    return {"ok": success}

