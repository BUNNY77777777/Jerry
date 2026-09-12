import asyncio
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool, BaseTool

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

# --- Pydantic Argument Schemas for LangGraph / LangChain tool invocation ---

class FetchUnreadEmailsInput(BaseModel):
    limit: int = Field(default=10, description="Max number of unread emails to fetch")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class SearchEmailsInput(BaseModel):
    query: str = Field(..., description="Gmail query search string (e.g. 'from:boss urgent' or 'contract')")
    limit: int = Field(default=10, description="Max search results to return")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class CreateEmailDraftInput(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email content body in plain text")
    thread_id: Optional[str] = Field(default=None, description="Optional thread ID to reply within")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class SendEmailInput(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email content body in plain text")
    thread_id: Optional[str] = Field(default=None, description="Optional thread ID to reply within")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class GetEmailThreadInput(BaseModel):
    thread_id: str = Field(..., description="The unique thread ID to retrieve messages from")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class CheckAvailabilityInput(BaseModel):
    time_min: str = Field(..., description="ISO 8601 string for start of window to check free/busy status")
    time_max: str = Field(..., description="ISO 8601 string for end of window to check free/busy status")
    calendar_id: str = Field(default="primary", description="Calendar identifier")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class CreateCalendarEventInput(BaseModel):
    summary: str = Field(..., description="Meeting title / subject")
    start_time: str = Field(..., description="Start time in ISO 8601 format (e.g., '2026-09-12T14:00:00Z')")
    end_time: str = Field(..., description="End time in ISO 8601 format (e.g., '2026-09-12T14:30:00Z')")
    attendees: Optional[List[str]] = Field(default_factory=list, description="List of attendee email addresses")
    description: Optional[str] = Field(default=None, description="Meeting agenda or description")
    calendar_id: str = Field(default="primary", description="Calendar identifier")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class RescheduleCalendarEventInput(BaseModel):
    event_id: str = Field(..., description="Unique ID of the calendar event to reschedule")
    new_start_time: str = Field(..., description="New start time in ISO 8601 format")
    new_end_time: str = Field(..., description="New end time in ISO 8601 format")
    calendar_id: str = Field(default="primary", description="Calendar identifier")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


class ListUpcomingEventsInput(BaseModel):
    max_results: int = Field(default=10, description="Max number of upcoming events to list")
    calendar_id: str = Field(default="primary", description="Calendar identifier")
    user_id: Optional[str] = Field(default=None, description="Target executive user ID")


def _sync_runner(coro):
    """Helper to run async tools synchronously when called by standard sync runners."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def get_all_mcp_tools() -> List[BaseTool]:
    """
    Unified registry function exporting all Gmail and Google Calendar tools
    wrapped as standard StructuredTools for LangGraph / LangChain nodes.
    """
    tools = [
        # Gmail tools
        StructuredTool.from_function(
            func=lambda limit=10, user_id=None: _sync_runner(fetch_unread_emails(limit=limit, user_id=user_id)),
            coroutine=fetch_unread_emails,
            name="fetch_unread_emails",
            description="Fetches recent unread emails and threads from the executive Gmail inbox.",
            args_schema=FetchUnreadEmailsInput,
        ),
        StructuredTool.from_function(
            func=lambda query, limit=10, user_id=None: _sync_runner(search_emails(query=query, limit=limit, user_id=user_id)),
            coroutine=search_emails,
            name="search_emails",
            description="Searches past emails across subject, sender, and body text.",
            args_schema=SearchEmailsInput,
        ),
        StructuredTool.from_function(
            func=lambda to, subject, body, thread_id=None, user_id=None: _sync_runner(create_email_draft(to=to, subject=subject, body=body, thread_id=thread_id, user_id=user_id)),
            coroutine=create_email_draft,
            name="create_email_draft",
            description="Creates an email draft in Gmail without sending it immediately.",
            args_schema=CreateEmailDraftInput,
        ),
        StructuredTool.from_function(
            func=lambda to, subject, body, thread_id=None, user_id=None: _sync_runner(send_email(to=to, subject=subject, body=body, thread_id=thread_id, user_id=user_id)),
            coroutine=send_email,
            name="send_email",
            description="Sends an email directly through Gmail. High risk action.",
            args_schema=SendEmailInput,
        ),
        StructuredTool.from_function(
            func=lambda thread_id, user_id=None: _sync_runner(get_email_thread(thread_id=thread_id, user_id=user_id)),
            coroutine=get_email_thread,
            name="get_email_thread",
            description="Fetches the full conversation thread history and messages from Gmail.",
            args_schema=GetEmailThreadInput,
        ),
        # Calendar tools
        StructuredTool.from_function(
            func=lambda time_min, time_max, calendar_id="primary", user_id=None: _sync_runner(check_availability(time_min=time_min, time_max=time_max, calendar_id=calendar_id, user_id=user_id)),
            coroutine=check_availability,
            name="check_availability",
            description="Checks Google Calendar free/busy status for conflicts in a time window.",
            args_schema=CheckAvailabilityInput,
        ),
        StructuredTool.from_function(
            func=lambda summary, start_time, end_time, attendees=None, description=None, calendar_id="primary", user_id=None: _sync_runner(create_calendar_event(summary=summary, start_time=start_time, end_time=end_time, attendees=attendees, description=description, calendar_id=calendar_id, user_id=user_id)),
            coroutine=create_calendar_event,
            name="create_calendar_event",
            description="Creates a Google Calendar event and sends invites to attendees.",
            args_schema=CreateCalendarEventInput,
        ),
        StructuredTool.from_function(
            func=lambda event_id, new_start_time, new_end_time, calendar_id="primary", user_id=None: _sync_runner(reschedule_calendar_event(event_id=event_id, new_start_time=new_start_time, new_end_time=new_end_time, calendar_id=calendar_id, user_id=user_id)),
            coroutine=reschedule_calendar_event,
            name="reschedule_calendar_event",
            description="Updates and reschedules a calendar event's start and end times.",
            args_schema=RescheduleCalendarEventInput,
        ),
        StructuredTool.from_function(
            func=lambda max_results=10, calendar_id="primary", user_id=None: _sync_runner(list_upcoming_events(max_results=max_results, calendar_id=calendar_id, user_id=user_id)),
            coroutine=list_upcoming_events,
            name="list_upcoming_events",
            description="Lists upcoming calendar events and meetings starting from now.",
            args_schema=ListUpcomingEventsInput,
        ),
    ]
    return tools
