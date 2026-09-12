from typing import Optional
from supabase import create_client, Client
from app.core.config import get_settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Returns a singleton instance of the Supabase client using the service role key."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured in environment."
            )
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client
