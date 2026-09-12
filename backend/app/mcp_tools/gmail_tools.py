import base64
import asyncio
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from app.core.google_auth import get_gmail_service


def _parse_message_payload(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to extract sender, subject, date, snippet, and body from Gmail message object."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    snippet = msg.get("snippet", "")
    
    # Extract plain body if present
    body = snippet
    parts = msg.get("payload", {}).get("parts", [])
    if parts:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
    elif msg.get("payload", {}).get("body", {}).get("data"):
        data = msg["payload"]["body"]["data"]
        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "sender": headers.get("from", "Unknown"),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", "No Subject"),
        "date": headers.get("date", ""),
        "snippet": snippet,
        "body": body,
        "labels": msg.get("labelIds", []),
    }


async def fetch_unread_emails(limit: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches recent unread inbox emails and threads from Gmail.
    """
    def _run():
        service = get_gmail_service(user_id=user_id)
        results = service.users().messages().list(
            userId="me",
            q="is:unread label:INBOX",
            maxResults=limit,
        ).execute()

        messages = results.get("messages", [])
        parsed_emails = []
        for m in messages:
            full_msg = service.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()
            parsed_emails.append(_parse_message_payload(full_msg))
        return parsed_emails

    return await asyncio.to_thread(_run)


async def search_emails(query: str, limit: int = 10, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches past emails across subject, sender, and body text using Gmail search syntax.
    """
    def _run():
        service = get_gmail_service(user_id=user_id)
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=limit,
        ).execute()

        messages = results.get("messages", [])
        parsed_emails = []
        for m in messages:
            full_msg = service.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()
            parsed_emails.append(_parse_message_payload(full_msg))
        return parsed_emails

    return await asyncio.to_thread(_run)


async def create_email_draft(
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates a draft in Gmail without sending it immediately.
    """
    def _run():
        service = get_gmail_service(user_id=user_id)
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft_body: Dict[str, Any] = {"message": {"raw": raw}}
        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        draft = service.users().drafts().create(userId="me", body=draft_body).execute()
        return {
            "draft_id": draft.get("id"),
            "message_id": draft.get("message", {}).get("id"),
            "status": "draft_created",
            "to": to,
            "subject": subject,
        }

    return await asyncio.to_thread(_run)


async def send_email(
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends an email directly through the Gmail API.
    """
    def _run():
        service = get_gmail_service(user_id=user_id)
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        send_body: Dict[str, Any] = {"raw": raw}
        if thread_id:
            send_body["threadId"] = thread_id

        sent_msg = service.users().messages().send(userId="me", body=send_body).execute()
        return {
            "id": sent_msg.get("id"),
            "threadId": sent_msg.get("threadId"),
            "status": "sent",
            "to": to,
            "subject": subject,
        }

    return await asyncio.to_thread(_run)


async def get_email_thread(thread_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches the complete conversation thread context for a specific thread_id.
    """
    def _run():
        service = get_gmail_service(user_id=user_id)
        thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        
        messages = thread.get("messages", [])
        parsed_thread_messages = [_parse_message_payload(m) for m in messages]

        return {
            "thread_id": thread.get("id"),
            "history_id": thread.get("historyId"),
            "messages_count": len(parsed_thread_messages),
            "messages": parsed_thread_messages,
        }

    return await asyncio.to_thread(_run)
