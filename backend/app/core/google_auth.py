import json
from typing import Any, Dict, Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.core.supabase import get_supabase_client
from app.core.config import get_settings

GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def get_user_credentials(user_id: Optional[str] = None, user_email: Optional[str] = None) -> Optional[Credentials]:
    """
    Retrieves and refreshes stored Google OAuth credentials for a user from Supabase.
    If no user_id is provided, attempts to load the most recently updated executive user.
    """
    supabase = get_supabase_client()
    settings = get_settings()

    query = supabase.table("users").select("*")
    if user_id:
        query = query.eq("id", user_id)
    elif user_email:
        query = query.eq("email", user_email)
    else:
        query = query.order("updated_at", desc=True).limit(1)

    res = query.execute()
    if not res.data or len(res.data) == 0:
        return None

    user_record = res.data[0]
    token_data = user_record.get("google_tokens")
    if not token_data or not isinstance(token_data, dict):
        return None

    token = token_data.get("token") or token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_uri = token_data.get("token_uri", "https://oauth2.googleapis.com/token")
    client_id = token_data.get("client_id") or settings.GOOGLE_CLIENT_ID
    client_secret = token_data.get("client_secret") or settings.GOOGLE_CLIENT_SECRET
    scopes = token_data.get("scopes") or GOOGLE_OAUTH_SCOPES

    if not token and not refresh_token:
        return None

    creds = Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )

    # Refresh token if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Update tokens in Supabase
            updated_tokens = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }
            supabase.table("users").update({"google_tokens": updated_tokens}).eq("id", user_record["id"]).execute()
        except Exception:
            pass

    return creds


def get_gmail_service(user_id: Optional[str] = None):
    """Builds an authorized Gmail API service client."""
    creds = get_user_credentials(user_id=user_id)
    if not creds:
        raise ValueError("No valid Google credentials found for user. Please authenticate via /api/auth/login.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def get_calendar_service(user_id: Optional[str] = None):
    """Builds an authorized Google Calendar API service client."""
    creds = get_user_credentials(user_id=user_id)
    if not creds:
        raise ValueError("No valid Google credentials found for user. Please authenticate via /api/auth/login.")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
