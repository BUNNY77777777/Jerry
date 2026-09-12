from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage
from app.agent.graph import agent_app

router = APIRouter(prefix="/api/command", tags=["Command"])


class CommandRequest(BaseModel):
    prompt: Optional[str] = None
    message: Optional[str] = None
    user_id: Optional[str] = "default-user"


class CommandResponse(BaseModel):
    status: str
    reply: str


@router.post("", response_model=CommandResponse)
def handle_command(payload: CommandRequest):
    user_prompt = payload.prompt or payload.message or "Hello"
    current_user_id = payload.user_id or "default-user"
    
    result = agent_app.invoke(
        {"messages": [HumanMessage(content=user_prompt)]},
        config={"configurable": {"user_id": current_user_id}}
    )
    ai_response = result["messages"][-1].content
    return CommandResponse(
        status="success",
        reply=ai_response,
    )
