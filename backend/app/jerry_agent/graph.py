from typing import Any, Dict, Literal
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from app.jerry_agent.state import JerryState
from app.jerry_agent.nodes import (
    calendar_node,
    communication_node,
    planner_node,
    triage_node,
    verification_node,
)
from app.jerry_agent.checkpointer import SupabaseCheckpointer
from app.governance.approval import create_approval_request


def human_approval_node(state: JerryState) -> Dict[str, Any]:
    """
    Human Approval Checkpoint Node:
      - If requires_approval is True or risk_score > 70, creates a pending approval record.
      - Returns status awaiting user input.
    """
    user_id = state.get("user_id", "default-user")
    intent = state.get("intent", "executive_action")
    proposed = state.get("proposed_actions", [])
    risk = state.get("risk_score", 85)

    try:
        create_approval_request(
            user_id=user_id,
            action_type=intent,
            payload={"proposed_actions": proposed, "state_snapshot": {"intent": intent}},
            risk_score=risk,
        )
    except Exception:
        pass

    return {
        "approval_status": "pending",
    }


def route_after_planner(state: JerryState) -> Literal["human_approval_node", "communication_node", "calendar_node", "verification_node", "__end__"]:
    """
    Conditional routing after planning:
      - If risk_score > 70 or requires_approval == True, route to human approval checkpoint.
      - If intent is communication -> route to communication_node.
      - If intent is calendar -> route to calendar_node.
      - Otherwise -> direct to verification_node.
    """
    risk_score = state.get("risk_score", 0)
    requires_approval = state.get("requires_approval", False)
    approval_status = state.get("approval_status", "")

    if approval_status == "rejected":
        return END

    if (risk_score > 70 or requires_approval) and approval_status != "approved":
        return "human_approval_node"

    intent = state.get("intent", "")
    if intent in ["reply_email", "send_email"]:
        return "communication_node"
    elif intent in ["schedule_meeting", "check_calendar_availability"]:
        return "calendar_node"
    
    return "verification_node"


def route_after_approval(state: JerryState) -> Literal["communication_node", "calendar_node", "verification_node", "__end__"]:
    """
    Evaluates approval decision:
      - If rejected: terminate safely or cancel.
      - If approved: proceed with execution nodes.
    """
    approval_status = state.get("approval_status", "pending")
    if approval_status == "rejected":
        return END

    intent = state.get("intent", "")
    if intent in ["reply_email", "send_email"]:
        return "communication_node"
    elif intent in ["schedule_meeting", "check_calendar_availability"]:
        return "calendar_node"

    return "verification_node"


def build_jerry_graph(checkpointer: Any = None):
    """
    Constructs the LangGraph StateGraph linking all nodes with human-in-the-loop interrupts.
    """
    workflow = StateGraph(JerryState)

    # 1. Add core nodes
    workflow.add_node("triage_node", triage_node)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("human_approval_node", human_approval_node)
    workflow.add_node("communication_node", communication_node)
    workflow.add_node("calendar_node", calendar_node)
    workflow.add_node("verification_node", verification_node)

    # 2. Connect Entrypoint
    workflow.set_entry_point("triage_node")
    workflow.add_edge("triage_node", "planner_node")

    # 3. Conditional routing from planner
    workflow.add_conditional_edges(
        "planner_node",
        route_after_planner,
        {
            "human_approval_node": "human_approval_node",
            "communication_node": "communication_node",
            "calendar_node": "calendar_node",
            "verification_node": "verification_node",
            END: END,
        }
    )

    # 4. Conditional routing after human approval
    workflow.add_conditional_edges(
        "human_approval_node",
        route_after_approval,
        {
            "communication_node": "communication_node",
            "calendar_node": "calendar_node",
            "verification_node": "verification_node",
            END: END,
        }
    )

    # 5. Connect domain execution nodes to verification
    workflow.add_edge("communication_node", "verification_node")
    workflow.add_edge("calendar_node", "verification_node")
    workflow.add_edge("verification_node", END)

    # Interrupt at human_approval_node to allow review/resume
    return workflow.compile(
        checkpointer=checkpointer or MemorySaver(),
        interrupt_before=["human_approval_node"],
    )


# Export standard compiled graph instances
jerry_memory_graph = build_jerry_graph(checkpointer=MemorySaver())
try:
    jerry_supabase_graph = build_jerry_graph(checkpointer=SupabaseCheckpointer())
except Exception:
    jerry_supabase_graph = jerry_memory_graph

__all__ = [
    "build_jerry_graph",
    "jerry_memory_graph",
    "jerry_supabase_graph",
]
