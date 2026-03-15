"""
FastAPI dependency injection for authentication.
Validates Supabase-issued JWTs and returns the authenticated user.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.supabase_client import get_supabase, get_supabase_anon

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> dict:
    """
    Extract user from Supabase JWT.
    Uses the anon client to call auth.get_user() which validates the token
    against Supabase Auth and returns the user object.
    Raises 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        client = get_supabase_anon()
        response = client.auth.get_user(credentials.credentials)
        if response is None or response.user is None:
            raise credentials_exception
        return response.user
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Extends get_current_user — additionally verifies the account is active
    by checking the public.users row.
    """
    user_id = current_user.id
    try:
        supabase = get_supabase()
        result = supabase.table("users").select("id, is_active").eq("id", str(user_id)).single().execute()
        if result.data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not result.data.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user
