from datetime import datetime, timezone
from typing import Any, Dict, List
from langchain.tools import tool
from app.services.google_service import get_calendar_service, get_gmail_service


@tool
def get_unread_emails(user_id: str) -> List[Dict[str, Any]]:
    """
    Fetches the top 5 unread emails for the specified user from Gmail.
    Returns a list of email dictionaries containing sender, subject, snippet, and id.
    """
    try:
        service = get_gmail_service(user_id)
        results = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=5)
            .execute()
        )
        messages = results.get("messages", [])

        emails = []
        for msg_summary in messages:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_summary["id"], format="full")
                .execute()
            )

            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            sender = "Unknown"
            subject = "No Subject"
            for header in headers:
                name = header.get("name", "").lower()
                if name == "from":
                    sender = header.get("value", sender)
                elif name == "subject":
                    subject = header.get("value", subject)

            snippet = msg.get("snippet", "")

            emails.append({
                "id": msg.get("id"),
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
            })

        return emails
    except Exception as e:
        return [{"error": f"Failed to retrieve unread emails: {str(e)}"}]


@tool
def get_todays_schedule(user_id: str) -> List[Dict[str, Any]]:
    """
    Fetches today's upcoming events from Google Calendar for the specified user.
    Returns a list of event dictionaries containing time, summary, and link.
    """
    try:
        service = get_calendar_service(user_id)
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        items = events_result.get("items", [])

        events = []
        for event in items:
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
            summary = event.get("summary", "Untitled Event")
            link = event.get("htmlLink", "")

            events.append({
                "id": event.get("id"),
                "summary": summary,
                "time": f"{start} - {end}" if end else start,
                "link": link,
            })

        return events
    except Exception as e:
        return [{"error": f"Failed to retrieve calendar schedule: {str(e)}"}]
