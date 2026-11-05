from pydantic import BaseModel
from fastapi import APIRouter

from services.command_core import interpret_command


router = APIRouter(prefix="/command", tags=["command"])


class CommandPayload(BaseModel):
    text: str
    site_id: str | None = None
    landmark_id: str | None = None


@router.post("/interpret")
def interpret(payload: CommandPayload) -> dict:
    return interpret_command(
        text=payload.text,
        site_id=payload.site_id,
        landmark_id=payload.landmark_id,
    )
