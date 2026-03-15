"""
Auth routes: register, login, refresh, me.
All auth operations are proxied to Supabase Auth.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator

from app.auth.dependencies import get_current_active_user
from app.supabase_client import get_supabase, get_supabase_anon

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request / Response Schemas ────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    subdomain: str | None
    plan: str


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
) -> TokenResponse:
    """Create a new user account via Supabase Auth and return session tokens."""
    supabase = get_supabase_anon()

    try:
        auth_response = supabase.auth.sign_up(
            {
                "email": body.email,
                "password": body.password,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {exc}",
        )

    if auth_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed — email may already be registered",
        )

    # Create the public.users profile row using service role (bypasses RLS)
    service_client = get_supabase()
    try:
        service_client.table("users").insert(
            {
                "id": str(auth_response.user.id),
                "email": body.email,
                "full_name": body.full_name,
                "is_active": True,
                "plan": "free",
            }
        ).execute()
    except Exception:
        # Profile row creation is best-effort; auth account already exists
        pass

    # Log audit event
    try:
        service_client.table("audit_logs").insert(
            {
                "user_id": str(auth_response.user.id),
                "event_type": "auth.register",
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_path": str(request.url.path),
                "request_method": "POST",
                "response_status": 201,
            }
        ).execute()
    except Exception:
        pass

    session = auth_response.session
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_201_CREATED,
            detail="Account created. Please verify your email before logging in.",
        )

    return TokenResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
) -> TokenResponse:
    """Authenticate user via Supabase Auth and return session tokens."""
    supabase = get_supabase_anon()

    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if auth_response.user is None or auth_response.session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account is active in public.users
    service_client = get_supabase()
    try:
        user_row = service_client.table("users").select("is_active").eq(
            "id", str(auth_response.user.id)
        ).single().execute()
        if user_row.data and not user_row.data.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
    except HTTPException:
        raise
    except Exception:
        pass

    # Audit log
    try:
        service_client.table("audit_logs").insert(
            {
                "user_id": str(auth_response.user.id),
                "event_type": "auth.login",
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_path": str(request.url.path),
                "request_method": "POST",
                "response_status": 200,
            }
        ).execute()
    except Exception:
        pass

    return TokenResponse(
        access_token=auth_response.session.access_token,
        refresh_token=auth_response.session.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
) -> TokenResponse:
    """Issue a new access token using a valid Supabase refresh token."""
    supabase = get_supabase_anon()

    try:
        auth_response = supabase.auth.refresh_session(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if auth_response.session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=auth_response.session.access_token,
        refresh_token=auth_response.session.refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> UserResponse:
    """Return the authenticated user's profile from public.users."""
    supabase = get_supabase()
    user_id = str(current_user.id)

    result = supabase.table("users").select(
        "id, email, full_name, is_active, subdomain, plan"
    ).eq("id", user_id).single().execute()

    if result.data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    data = result.data
    return UserResponse(
        id=data["id"],
        email=data["email"],
        full_name=data.get("full_name"),
        is_active=data.get("is_active", True),
        subdomain=data.get("subdomain"),
        plan=data.get("plan", "free"),
    )
