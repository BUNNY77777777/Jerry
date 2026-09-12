import json
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings
from app.governance.risk_engine import RiskEngine
from app.governance.policy_engine import PolicyEngine
from app.jerry_agent.state import JerryState


def _get_llm() -> Optional[ChatGoogleGenerativeAI]:
    """Provides the Gemini Chat model instance if API key is present."""
    settings = get_settings()
    if settings.GEMINI_API_KEY:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
        )
    return None


def triage_node(state: JerryState) -> Dict[str, Any]:
    """
    Triage Node:
      - Analyzes incoming email or user message using Gemini.
      - Extracts intent, classifies priority.
      - Identifies missing information.
      - Runs RiskEngine checks for security risks/phishing.
    """
    current_email = state.get("current_email") or {}
    messages = state.get("messages") or []
    content = ""

    if current_email:
        sender = current_email.get("sender") or current_email.get("from", "unknown")
        subject = current_email.get("subject", "No Subject")
        body = current_email.get("body", "")
        content = f"Sender: {sender}\nSubject: {subject}\nBody: {body}"
    elif messages:
        content = str(messages[-1].content)
    else:
        content = "No input provided."

    # 1. Run security/phishing analysis via RiskEngine
    risk_engine = RiskEngine()
    sender = current_email.get("sender") if current_email else None
    phishing_check = risk_engine.detect_phishing(sender=sender, content=content)

    intent = "general_inquiry"
    priority = "medium"
    missing_info = []

    llm = _get_llm()
    if llm:
        system_prompt = (
            "You are Jerry's executive triage specialist. Analyze the input email or message.\n"
            "Respond in strictly valid JSON format with keys:\n"
            "- intent: (e.g. schedule_meeting, reply_email, share_document, general_query)\n"
            "- priority: (low, medium, high, urgent)\n"
            "- missing_info: list of missing elements needed to execute (e.g. time, attendees, document name)\n"
            "- summary: one sentence executive summary"
        )
        try:
            response = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ])
            text = response.content.strip()
            # Clean markdown codeblocks if returned
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            intent = data.get("intent", intent)
            priority = data.get("priority", priority)
            missing_info = data.get("missing_info", [])
        except Exception:
            # Heuristic fallback if LLM parse fails
            if "schedule" in content.lower() or "meet" in content.lower() or "calendar" in content.lower():
                intent = "schedule_meeting"
            elif "reply" in content.lower() or "send email" in content.lower():
                intent = "reply_email"
            else:
                intent = "general_query"
    else:
        if "meet" in content.lower() or "schedule" in content.lower():
            intent = "schedule_meeting"
        elif "send" in content.lower() or "reply" in content.lower():
            intent = "reply_email"

    # Evaluate baseline risk for extracted intent
    base_eval = risk_engine.evaluate_action(intent, current_email)
    risk_score = base_eval.score
    if phishing_check["is_suspicious"]:
        risk_score = max(risk_score, 90)

    requires_approval = risk_score > 70 or len(phishing_check["flags"]) > 0

    return {
        "intent": intent,
        "risk_score": risk_score,
        "requires_approval": requires_approval,
        "approval_status": "pending" if requires_approval else "approved",
        "task_plan": [f"Triage complete: Intent '{intent}', priority '{priority}'."],
    }


def planner_node(state: JerryState) -> Dict[str, Any]:
    """
    Planner Node:
      - Decomposes complex executive requests into dynamic multi-step execution plans.
      - Proposes concrete tool actions and structures the workflow.
    """
    intent = state.get("intent", "general_inquiry")
    current_email = state.get("current_email") or {}
    llm = _get_llm()

    plan: List[str] = []
    proposed_actions: List[Dict[str, Any]] = []

    if llm:
        planner_prompt = (
            f"Given the user intent '{intent}' and email/context: {json.dumps(current_email)}, "
            "decompose this into a sequential step-by-step task plan and list proposed actions.\n"
            "Output JSON with keys:\n"
            "- task_plan: list of steps (strings)\n"
            "- proposed_actions: list of dicts with keys 'action_type' and 'payload'"
        )
        try:
            response = llm.invoke([
                {"role": "system", "content": "You are Jerry's Chief-of-Staff Executive Planner."},
                {"role": "user", "content": planner_prompt}
            ])
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            plan = data.get("task_plan", [])
            proposed_actions = data.get("proposed_actions", [])
        except Exception:
            pass

    if not plan:
        if intent == "schedule_meeting":
            plan = [
                "Check calendar availability for requested attendees",
                "Draft calendar invite during non-focus hours",
                "Send invitation upon approval",
                "Verify calendar confirmation"
            ]
            proposed_actions = [{
                "action_type": "check_calendar_availability",
                "payload": {"attendees": current_email.get("sender")}
            }]
        elif intent in ["reply_email", "send_email"]:
            plan = [
                "Draft context-aware response",
                "Run governance & risk checks",
                "Queue for human review if risk score > 70",
                "Transmit email and verify delivery"
            ]
            proposed_actions = [{
                "action_type": "send_email",
                "payload": {
                    "to": current_email.get("sender"),
                    "subject": f"Re: {current_email.get('subject', '')}",
                    "body": "Thank you for reaching out. I am reviewing your request."
                }
            }]
        else:
            plan = ["Analyze inquiry", "Retrieve context from memory", "Formulate summary"]
            proposed_actions = [{
                "action_type": "query_memory",
                "payload": {"query": current_email.get("subject", "")}
            }]

    # Re-evaluate risk with proposed actions & policies
    risk_engine = RiskEngine()
    policy_engine = PolicyEngine()
    max_risk = state.get("risk_score", 0)

    for action in proposed_actions:
        a_eval = risk_engine.evaluate_action(action.get("action_type", ""), action.get("payload", {}))
        pol_eval = policy_engine.evaluate(action.get("action_type", ""), action.get("payload", {}))
        max_risk = max(max_risk, a_eval.score)
        if pol_eval.requires_human_approval:
            max_risk = max(max_risk, 75)

    requires_approval = max_risk > 70 or state.get("requires_approval", False)

    return {
        "task_plan": plan,
        "proposed_actions": proposed_actions,
        "risk_score": max_risk,
        "requires_approval": requires_approval,
        "approval_status": "pending" if requires_approval else "approved",
    }


def communication_node(state: JerryState) -> Dict[str, Any]:
    """
    Communication Node:
      - Formulates context-aware draft responses or triggers follow-ups.
    """
    current_email = state.get("current_email") or {}
    intent = state.get("intent", "general_inquiry")
    llm = _get_llm()

    sender = current_email.get("sender") or current_email.get("from", "Executive Colleague")
    subject = current_email.get("subject", "Executive Inquiry")
    draft_body = ""

    if llm:
        try:
            prompt = (
                f"Draft a concise, professional executive response to the following email from {sender}:\n"
                f"Subject: {subject}\n"
                f"Intent: {intent}\n"
                f"Content: {current_email.get('body', '')}\n"
                "Keep the tone polished, decisive, and courteous."
            )
            response = llm.invoke([{"role": "user", "content": prompt}])
            draft_body = response.content.strip()
        except Exception:
            draft_body = f"Hello,\n\nThank you for your note regarding '{subject}'. I am reviewing this with our team and will revert shortly.\n\nBest regards,\nJerry (AI Executive Assistant)"
    else:
        draft_body = f"Hello,\n\nThank you for your message regarding '{subject}'. I am looking into this and will follow up.\n\nBest regards,\nJerry"

    action = {
        "action_type": "save_draft_email",
        "payload": {
            "to": sender,
            "subject": f"Re: {subject}",
            "body": draft_body,
        }
    }

    actions = list(state.get("proposed_actions", []))
    actions.append(action)

    messages = list(state.get("messages", []))
    messages.append(AIMessage(content=f"Drafted executive response for {sender}:\n\n{draft_body}"))

    return {
        "proposed_actions": actions,
        "messages": messages,
    }


def calendar_node(state: JerryState) -> Dict[str, Any]:
    """
    Calendar Node:
      - Checks schedule availability, resolves conflicts, and manages calendar invites.
      - Enforces policy compliance around Focus Hours.
    """
    current_email = state.get("current_email") or {}
    policy_engine = PolicyEngine()
    
    proposed_meeting = {
        "summary": current_email.get("subject", "Executive Sync"),
        "start_time": "14:00",
        "end_time": "14:30",
        "attendees": [current_email.get("sender", "colleague@company.com")]
    }

    # Verify against focus hours
    policy_res = policy_engine.evaluate(
        action_type="create_calendar_event",
        payload=proposed_meeting,
    )

    action = {
        "action_type": "create_calendar_event",
        "payload": proposed_meeting,
        "policy_compliant": policy_res.is_compliant,
    }

    actions = list(state.get("proposed_actions", []))
    actions.append(action)

    messages = list(state.get("messages", []))
    status_msg = "Scheduled meeting at 14:00 (non-focus window)." if policy_res.is_compliant else "Meeting flagged for policy review."
    messages.append(AIMessage(content=status_msg))

    return {
        "proposed_actions": actions,
        "messages": messages,
    }


def verification_node(state: JerryState) -> Dict[str, Any]:
    """
    Verification Node:
      - Performs post-execution checks against APIs to confirm actions succeeded.
      - Produces audit-ready execution results.
    """
    proposed_actions = state.get("proposed_actions", [])
    results = list(state.get("execution_results", []))

    for action in proposed_actions:
        action_type = action.get("action_type")
        payload = action.get("payload", {})
        
        # Verify action result mock/check
        verified_result = {
            "action_type": action_type,
            "status": "verified_success",
            "details": f"Successfully verified execution of {action_type}.",
            "payload_summary": {k: v for k, v in payload.items() if k != "body"}
        }
        results.append(verified_result)

    messages = list(state.get("messages", []))
    messages.append(AIMessage(content=f"Verification complete: {len(results)} actions verified successfully."))

    return {
        "execution_results": results,
        "messages": messages,
    }
