"""
FastAPI dependency injection for authentication.
Provides get_current_user and get_current_active_user.
"""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import verify_token
from app.database import get_db, set_rls_user
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Extract and validate Bearer JWT token, return the authenticated User.
    Sets the RLS user context for Row-Level Security enforcement.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials, expected_type="access")
        user_id = payload.sub
    except JWTError:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise credentials_exception

    # Set RLS context BEFORE querying
    await set_rls_user(db, str(user_uuid))

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Extends get_current_user — additionally verifies the account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user
