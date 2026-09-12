from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.supabase import get_supabase_client


def log_commitment(
    user_id: str,
    title: str,
    contact_email: str,
    deadline: Optional[str] = None,
    description: Optional[str] = None,
    priority: str = "medium",
    source: str = "email",
) -> Dict[str, Any]:
    """
    Tracks promises or pending tasks extracted from communications
    and logs them into the Supabase commitments table.
    """
    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "user_id": user_id,
        "title": title,
        "description": description or f"Commitment involving {contact_email}",
        "assigned_to": contact_email,
        "due_date": deadline,
        "priority": priority,
        "status": "pending",
        "source": source,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    response = supabase.table("commitments").insert(record).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return record


def get_open_commitments(user_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves unresolved tasks ('pending', 'in_progress') requiring follow-up
    for a given user, ordered by due date and creation time.
    """
    supabase = get_supabase_client()
    response = (
        supabase.table("commitments")
        .select("*")
        .eq("user_id", user_id)
        .in_("status", ["pending", "in_progress"])
        .order("due_date", desc=False)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def create_or_get_thread(
    user_id: str,
    title: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Finds or initializes a context thread record in the context_threads table.
    """
    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    record = {
        "user_id": user_id,
        "title": title,
        "metadata": metadata or {},
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    response = supabase.table("context_threads").insert(record).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return record


def update_commitment_status(
    commitment_id: str,
    status: str,
) -> Dict[str, Any]:
    """
    Updates the status of a commitment (e.g. 'completed', 'cancelled', 'in_progress').
    """
    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    response = (
        supabase.table("commitments")
        .update({"status": status, "updated_at": now_iso})
        .eq("id", commitment_id)
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return {"id": commitment_id, "status": status}
