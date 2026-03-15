"""
Omi OAuth 2.0 authorization flow.

Omi uses OAuth 2.0 to allow third-party apps (like Character-Websites) to access
a user's Omi cloud data (conversations/recordings, speech profile).

Flow:
1. User visits our app's pairing page
2. We redirect them to the Omi OAuth authorization page with our app_id + scopes
3. User approves — Omi redirects back with an authorization code
4. We exchange the code for an access_token + refresh_token
5. We store device_id + omi_access_token + omi_refresh_token in our backend DB

Omi's OAuth endpoints (from the open-source backend):
  - GET  /v1/oauth/authorize?app_id=...&state=...     → shows consent page
  - POST /v1/oauth/token                              → exchange code for tokens

Reference: https://github.com/BasedHardware/omi/blob/main/backend/routers/oauth.py
"""
import hashlib
import secrets
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx

from omi.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OmiTokens:
    """Tokens returned by the Omi OAuth flow."""
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: Optional[int]           # seconds until access_token expires
    scope: str
    uid: Optional[str] = None           # Omi user UID (Firebase UID)
    obtained_at: datetime = None        # when we got these tokens

    def __post_init__(self):
        if self.obtained_at is None:
            self.obtained_at = datetime.now(timezone.utc)

    @property
    def expires_at(self) -> Optional[datetime]:
        if self.expires_in is None:
            return None
        return self.obtained_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        # Consider expired 60s before actual expiry
        return datetime.now(timezone.utc) >= self.expires_at - timedelta(seconds=60)

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "scope": self.scope,
            "uid": self.uid,
            "obtained_at": self.obtained_at.isoformat() if self.obtained_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OmiTokens":
        obtained_at = None
        if data.get("obtained_at"):
            obtained_at = datetime.fromisoformat(data["obtained_at"])
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope", ""),
            uid=data.get("uid"),
            obtained_at=obtained_at,
        )


class OmiOAuthClient:
    """
    Handles the Omi OAuth 2.0 authorization code flow.

    Usage:
        client = OmiOAuthClient()

        # Step 1: Redirect user to Omi authorization page
        auth_url, state = client.get_authorization_url()
        # redirect user to auth_url, store state for CSRF check

        # Step 2: Handle callback
        tokens = await client.exchange_code(code=request.query_params["code"])

        # Step 3: Refresh if needed
        if tokens.is_expired:
            tokens = await client.refresh_tokens(tokens.refresh_token)
    """

    def __init__(self):
        self.settings = get_settings()
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "CharacterWebsites/1.0"},
            )
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def get_authorization_url(self, extra_state: Optional[str] = None) -> tuple[str, str]:
        """
        Build the Omi OAuth authorization URL.

        Returns:
            (authorization_url, state_token)
            Store state_token in the user's session to validate the callback.
        """
        # CSRF state token: random + optional user data
        state = secrets.token_urlsafe(32)
        if extra_state:
            # Embed extra state in the state param (e.g. user_id for post-callback linking)
            # Hash to prevent tampering; decode on callback by looking up in Redis/session
            state = f"{state}.{hashlib.sha256(extra_state.encode()).hexdigest()[:8]}"

        params = {
            "app_id": self.settings.OMI_APP_ID,
            "state": state,
        }

        # The Omi OAuth page is a browser-based consent UI — redirect_uri is configured
        # in the Omi developer portal for our app_id
        auth_url = f"{self.settings.OMI_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

        logger.info(f"Generated OAuth authorization URL for app_id={self.settings.OMI_APP_ID}")
        return auth_url, state

    async def exchange_code(self, code: str) -> OmiTokens:
        """
        Exchange the authorization code for access and refresh tokens.

        Called on the OAuth callback endpoint after the user approves the app.
        """
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.settings.OMI_CLIENT_ID,
            "redirect_uri": self.settings.OMI_OAUTH_REDIRECT_URI,
        }
        # client_secret is optional for Omi public apps
        if self.settings.OMI_CLIENT_SECRET:
            payload["client_secret"] = self.settings.OMI_CLIENT_SECRET

        logger.info("Exchanging OAuth authorization code for tokens")

        try:
            response = await self.http_client.post(
                self.settings.OMI_OAUTH_TOKEN_URL,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"OAuth token exchange failed: {exc.response.status_code} "
                f"{exc.response.text}"
            )
            raise OmiAuthError(
                f"Token exchange failed: {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"OAuth token exchange request failed: {exc}")
            raise OmiAuthError(f"Token exchange request error: {exc}") from exc

        data = response.json()

        tokens = OmiTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope", self.settings.OMI_OAUTH_SCOPES),
            uid=data.get("uid"),
        )

        logger.info(f"Successfully obtained tokens for uid={tokens.uid}")
        return tokens

    async def refresh_tokens(self, refresh_token: str) -> OmiTokens:
        """
        Use a refresh token to obtain a new access token.
        """
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.settings.OMI_CLIENT_ID,
            "client_secret": self.settings.OMI_CLIENT_SECRET,
        }

        logger.info("Refreshing Omi OAuth tokens")

        try:
            response = await self.http_client.post(
                self.settings.OMI_OAUTH_TOKEN_URL,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Token refresh failed: {exc.response.status_code} {exc.response.text}")
            raise OmiAuthError(f"Token refresh failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise OmiAuthError(f"Token refresh request error: {exc}") from exc

        data = response.json()
        tokens = OmiTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),  # keep old if not rotated
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            scope=data.get("scope", self.settings.OMI_OAUTH_SCOPES),
            uid=data.get("uid"),
        )
        logger.info("Successfully refreshed tokens")
        return tokens

    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke an access token (called on device de-pairing).
        Omi may not expose a revocation endpoint — log and treat as success if not.
        """
        revoke_url = f"{self.settings.OMI_API_BASE_URL}/v1/oauth/revoke"
        try:
            response = await self.http_client.post(
                revoke_url,
                json={"token": access_token},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if response.status_code in (200, 204):
                logger.info("Successfully revoked Omi access token")
                return True
            # 404 = endpoint doesn't exist (acceptable)
            if response.status_code == 404:
                logger.warning("Omi revocation endpoint not found — treating as revoked")
                return True
            logger.error(f"Token revocation returned unexpected status: {response.status_code}")
            return False
        except httpx.RequestError as exc:
            logger.error(f"Token revocation request failed: {exc}")
            return False

    async def get_user_profile(self, access_token: str) -> dict:
        """
        Fetch the Omi user profile using the access token.
        Returns uid, name, email from Omi cloud.
        """
        try:
            response = await self.http_client.get(
                f"{self.settings.OMI_API_BASE_URL}/v1/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Failed to fetch user profile: {exc.response.status_code}")
            raise OmiAuthError(f"Profile fetch failed: {exc.response.status_code}") from exc


class OmiAuthError(Exception):
    """Raised when Omi OAuth operations fail."""
    pass
