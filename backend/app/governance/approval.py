from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.supabase import get_supabase_client
from app.schemas.governance import ApprovalStatus


def create_approval_request(
    user_id: str,
    action_type: str,
    payload: Dict[str, Any],
    risk_score: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Inserts a pending approval record into the Supabase approval_queue table.
    Enriches the payload with risk_score and metadata.
    """
    supabase = get_supabase_client()
    enriched_payload = dict(payload)
    if risk_score is not None:
        enriched_payload["_risk_score"] = risk_score

    record = {
        "user_id": user_id,
        "action_type": action_type,
        "payload": enriched_payload,
        "status": ApprovalStatus.PENDING.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    response = supabase.table("approval_queue").insert(record).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return record


def get_pending_approvals(user_id: str) -> List[Dict[str, Any]]:
    """
    Fetches active pending approval requests awaiting user decision for a given user.
    """
    supabase = get_supabase_client()
    response = (
        supabase.table("approval_queue")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", ApprovalStatus.PENDING.value)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def resolve_approval(
    request_id: str,
    status: str,
    approved_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates the status of an approval request to 'approved' or 'rejected'.
    Validates status parameter and sets reviewed_at timestamp.
    """
    normalized_status = status.lower().strip()
    if normalized_status not in [ApprovalStatus.APPROVED.value, ApprovalStatus.REJECTED.value]:
        raise ValueError(
            f"Invalid status '{status}'. Status must be '{ApprovalStatus.APPROVED.value}' or '{ApprovalStatus.REJECTED.value}'."
        )

    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    update_payload = {
        "status": normalized_status,
        "reviewed_at": now_iso,
    }
    if approved_by:
        update_payload["approved_by"] = approved_by

    response = (
        supabase.table("approval_queue")
        .update(update_payload)
        .eq("id", request_id)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]
    return {"id": request_id, **update_payload}
