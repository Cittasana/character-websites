"""
JWT token creation/validation and password hashing utilities.
Uses python-jose for JWT and passlib[bcrypt] for password hashing.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ── Password Hashing ──────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── Token Creation ─────────────────────────────────────────────────────────────
def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Internal helper — create a signed JWT token."""
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # JWT ID for token revocation tracking
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived access token (default 60 minutes)."""
    return _create_token(
        subject=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"email": email},
    )


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh token (default 30 days)."""
    return _create_token(
        subject=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


# ── Token Validation ──────────────────────────────────────────────────────────
class TokenPayload:
    """Parsed, validated token payload."""

    def __init__(self, sub: str, token_type: str, jti: str, **kwargs: Any) -> None:
        self.sub = sub
        self.token_type = token_type
        self.jti = jti
        self.extra = kwargs


def verify_token(token: str, expected_type: str = "access") -> TokenPayload:
    """
    Verify and decode a JWT token.
    Raises JWTError if the token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise JWTError(f"Token validation failed: {exc}") from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise JWTError(
            f"Invalid token type: expected '{expected_type}', got '{token_type}'"
        )

    sub = payload.get("sub")
    if not sub:
        raise JWTError("Token missing 'sub' claim")

    jti = payload.get("jti", "")
    return TokenPayload(sub=sub, token_type=token_type, jti=jti, **{
        k: v for k, v in payload.items() if k not in ("sub", "type", "jti", "iat", "exp")
    })
