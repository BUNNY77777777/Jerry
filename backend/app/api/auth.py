from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.core.config import get_settings
from app.core.supabase import get_supabase_client
from app.core.google_auth import GOOGLE_OAUTH_SCOPES, get_user_credentials

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _create_oauth_flow(redirect_uri: Optional[str] = None) -> Flow:
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) are not configured.",
        )

    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=GOOGLE_OAUTH_SCOPES,
        redirect_uri=redirect_uri or settings.GOOGLE_REDIRECT_URI,
    )
    return flow


@router.get("/login")
def login(state: Optional[str] = None):
    """
    GET /api/auth/login
    Generates the Google OAuth authorization URL requesting scopes for Gmail, Calendar, and profile,
    and redirects the user directly to Google's consent screen.
    """
    flow = _create_oauth_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state or "jerry_auth",
    )
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
def oauth2_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None),
):
    """
    GET /api/auth/callback
    Handles the OAuth2 redirect code, exchanges it for access/refresh tokens,
    retrieves the user's Google profile, and saves the tokens to the Supabase users table.
    """
    settings = get_settings()
    supabase = get_supabase_client()

    try:
        flow = _create_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Retrieve user profile from Google OAuth2
        oauth2_service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
        user_info = oauth2_service.userinfo().get().execute()

        email = user_info.get("email")
        full_name = user_info.get("name", "Executive")
        picture = user_info.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Google profile.")

        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

        # Upsert user record in Supabase
        now_iso = datetime.now(timezone.utc).isoformat()
        user_query = supabase.table("users").select("*").eq("email", email).execute()

        if user_query.data and len(user_query.data) > 0:
            user_id = user_query.data[0]["id"]
            supabase.table("users").update({
                "google_tokens": token_data,
                "full_name": full_name,
                "metadata": {"picture": picture, "google_user_info": user_info},
                "updated_at": now_iso,
            }).eq("id", user_id).execute()
        else:
            insert_res = supabase.table("users").insert({
                "email": email,
                "full_name": full_name,
                "role": "executive",
                "google_tokens": token_data,
                "metadata": {"picture": picture, "google_user_info": user_info},
                "created_at": now_iso,
                "updated_at": now_iso,
            }).execute()
            user_id = insert_res.data[0]["id"] if insert_res.data else None

        # Return status or redirect to frontend dashboard if running
        return {
            "status": "authenticated",
            "message": "Google OAuth2 authorization successful.",
            "email": email,
            "user_id": user_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with Google: {str(e)}")


@router.get("/status")
def auth_status(user_id: Optional[str] = Query(None), email: Optional[str] = Query(None)):
    """
    GET /api/auth/status
    Checks if valid Google tokens exist for the user.
    """
    try:
        creds = get_user_credentials(user_id=user_id, user_email=email)
        if creds and (creds.valid or creds.refresh_token):
            return {
                "authenticated": True,
                "token_expired": creds.expired,
                "has_refresh_token": bool(creds.refresh_token),
                "scopes": creds.scopes,
            }
        return {
            "authenticated": False,
            "message": "No active Google credentials found. Please authenticate via /api/auth/login.",
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e),
        }
