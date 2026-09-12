"""MCP Tools module for Jerry Executive Agent: Gmail, Calendar, and unified registry."""

from app.mcp_tools.gmail_tools import (
    fetch_unread_emails,
    search_emails,
    create_email_draft,
    send_email,
    get_email_thread,
)
from app.mcp_tools.calendar_tools import (
    check_availability,
    create_calendar_event,
    reschedule_calendar_event,
    list_upcoming_events,
)
from app.mcp_tools.registry import get_all_mcp_tools

__all__ = [
    "fetch_unread_emails",
    "search_emails",
    "create_email_draft",
    "send_email",
    "get_email_thread",
    "check_availability",
    "create_calendar_event",
    "reschedule_calendar_event",
    "list_upcoming_events",
    "get_all_mcp_tools",
]
