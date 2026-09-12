from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/command", tags=["Command"])


class CommandRequest(BaseModel):
    prompt: str


class CommandResponse(BaseModel):
    status: str
    reply: str


@router.post("", response_model=CommandResponse)
def handle_command(payload: CommandRequest):
    return CommandResponse(
        status="success",
        reply=f"Jerry processing command: {payload.prompt}",
    )
