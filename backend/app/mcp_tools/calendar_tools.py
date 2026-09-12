import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.google_auth import get_calendar_service


async def check_availability(
    time_min: str,
    time_max: str,
    calendar_id: str = "primary",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Checks free/busy status for conflicts within the specified time window.
    time_min and time_max should be ISO 8601 strings (e.g. 2026-09-12T09:00:00Z).
    """
    def _run():
        service = get_calendar_service(user_id=user_id)
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id}],
        }
        res = service.freebusy().query(body=body).execute()
        calendars = res.get("calendars", {})
        busy_slots = calendars.get(calendar_id, {}).get("busy", [])
        return {
            "calendar_id": calendar_id,
            "time_min": time_min,
            "time_max": time_max,
            "is_free": len(busy_slots) == 0,
            "busy_slots": busy_slots,
            "conflict_count": len(busy_slots),
        }

    return await asyncio.to_thread(_run)


async def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    calendar_id: str = "primary",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Books a new calendar event and sends invitation emails to attendees.
    start_time and end_time should be ISO 8601 format strings.
    """
    def _run():
        service = get_calendar_service(user_id=user_id)
        event_attendees = [{"email": a} for a in (attendees or [])]

        event_body = {
            "summary": summary,
            "description": description or "Scheduled via Jerry AI Executive Agent",
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
            "attendees": event_attendees,
            "reminders": {
                "useDefault": True,
            },
        }

        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            sendUpdates="all",
        ).execute()

        return {
            "event_id": created_event.get("id"),
            "html_link": created_event.get("htmlLink"),
            "summary": created_event.get("summary"),
            "status": created_event.get("status"),
            "start": created_event.get("start"),
            "end": created_event.get("end"),
            "attendees": [a.get("email") for a in created_event.get("attendees", [])],
        }

    return await asyncio.to_thread(_run)


async def reschedule_calendar_event(
    event_id: str,
    new_start_time: str,
    new_end_time: str,
    calendar_id: str = "primary",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates an existing calendar event's start and end times and notifies attendees.
    """
    def _run():
        service = get_calendar_service(user_id=user_id)
        # Fetch current event details
        existing_event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        existing_event["start"] = {"dateTime": new_start_time}
        existing_event["end"] = {"dateTime": new_end_time}

        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=existing_event,
            sendUpdates="all",
        ).execute()

        return {
            "event_id": updated_event.get("id"),
            "summary": updated_event.get("summary"),
            "status": updated_event.get("status"),
            "new_start": updated_event.get("start"),
            "new_end": updated_event.get("end"),
            "updated": updated_event.get("updated"),
        }

    return await asyncio.to_thread(_run)


async def list_upcoming_events(
    max_results: int = 10,
    calendar_id: str = "primary",
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetches upcoming calendar commitments starting from now.
    """
    def _run():
        service = get_calendar_service(user_id=user_id)
        now = datetime.now(timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        items = events_result.get("items", [])
        parsed_events = []
        for e in items:
            parsed_events.append({
                "id": e.get("id"),
                "summary": e.get("summary", "No Title"),
                "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
                "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
                "html_link": e.get("htmlLink"),
                "attendees": [a.get("email") for a in e.get("attendees", [])],
                "description": e.get("description", ""),
            })
        return parsed_events

    return await asyncio.to_thread(_run)
