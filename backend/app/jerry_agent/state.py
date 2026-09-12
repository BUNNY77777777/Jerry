from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage


class JerryState(TypedDict, total=False):
    """
    Central state definition for Jerry, the AI Executive Agent,
    orchestrated through LangGraph.
    """
    user_id: str
    messages: List[BaseMessage]
    current_email: Dict[str, Any]
    intent: str
    task_plan: List[str]
    proposed_actions: List[Dict[str, Any]]
    risk_score: int
    requires_approval: bool
    approval_status: str  # "pending" | "approved" | "rejected"
    execution_results: List[Dict[str, Any]]
