from typing import Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from app.core.supabase import get_supabase_client
from app.core.config import get_settings


def get_user_google_credentials(user_id: str) -> Optional[Credentials]:
    """
    Fetches the user's Google OAuth2 tokens from Supabase and constructs a Credentials object.
    """
    supabase = get_supabase_client()
    settings = get_settings()

    res = supabase.table("users").select("google_tokens").eq("id", user_id).execute()
    if not res.data or len(res.data) == 0:
        return None

    token_data = res.data[0].get("google_tokens")
    if not token_data or not isinstance(token_data, dict):
        return None

    token = token_data.get("token") or token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_uri = token_data.get("token_uri", "https://oauth2.googleapis.com/token")
    client_id = token_data.get("client_id") or settings.GOOGLE_CLIENT_ID
    client_secret = token_data.get("client_secret") or settings.GOOGLE_CLIENT_SECRET
    scopes = token_data.get("scopes")

    if not token and not refresh_token:
        return None

    return Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )


def get_gmail_service(user_id: str) -> Resource:
    """
    Builds and returns an authorized Google API discovery client for Gmail v1.
    """
    credentials = get_user_google_credentials(user_id)
    if not credentials:
        raise ValueError(f"No valid Google credentials found for user {user_id}")
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def get_calendar_service(user_id: str) -> Resource:
    """
    Builds and returns an authorized Google API discovery client for Calendar v3.
    """
    credentials = get_user_google_credentials(user_id)
    if not credentials:
        raise ValueError(f"No valid Google credentials found for user {user_id}")
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)
