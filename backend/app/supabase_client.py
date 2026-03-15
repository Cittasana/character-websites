"""
Supabase client factory.
Replaces the old SQLAlchemy database.py — no connection pool needed,
supabase-py manages HTTP connections internally.
"""
from supabase import Client, create_client

from app.config import get_settings


def get_supabase() -> Client:
    """
    Service role client — used by backend workers and FastAPI routes.
    Bypasses RLS — safe because we always filter by user_id explicitly.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon() -> Client:
    """
    Anon client — for operations that should respect RLS
    and for Supabase Auth token validation.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def check_supabase_health() -> bool:
    """Health check — returns True if Supabase is reachable."""
    try:
        client = get_supabase()
        # A lightweight query against a small table to verify connectivity
        client.table("users").select("id").limit(1).execute()
        return True
    except Exception:
        return False
