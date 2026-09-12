from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.agent.graph import agent_app

router = APIRouter(prefix="/api/command", tags=["Command"])


class CommandRequest(BaseModel):
    prompt: str
    user_id: str


class CommandResponse(BaseModel):
    status: str
    reply: str


@router.post("", response_model=CommandResponse)
def handle_command(payload: CommandRequest):
    result = agent_app.invoke(
        {"messages": [HumanMessage(content=payload.prompt)]},
        config={"configurable": {"user_id": payload.user_id}}
    )
    ai_response = result["messages"][-1].content
    return CommandResponse(
        status="success",
        reply=ai_response,
    )
