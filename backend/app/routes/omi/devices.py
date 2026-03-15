"""
Omi device pairing endpoints.

POST   /api/omi/devices              — store device pairing {device_id, omi_access_token}
GET    /api/omi/devices/:userId      — get device pairing status
PATCH  /api/omi/devices/:userId      — update omi_access_token (re-pair)
DELETE /api/omi/devices/:userId      — unpair device
GET    /api/omi/sync/status/:userId  — sync summary for a user
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_active_user
from app.supabase_client import get_supabase

router = APIRouter(prefix="/api/omi", tags=["omi"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class DevicePairRequest(BaseModel):
    device_id: str
    omi_access_token: str


class DevicePairResponse(BaseModel):
    user_id: uuid.UUID
    device_id: str
    paired: bool
    paired_at: str | None


class DeviceUpdateRequest(BaseModel):
    omi_access_token: str


class SyncStatusResponse(BaseModel):
    user_id: uuid.UUID
    last_sync_at: str | None
    recordings_count: int
    pending_uploads: int
    sync_enabled: bool


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/devices",
    response_model=DevicePairResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pair an Omi device",
    description="Store device_id and omi_access_token for the authenticated user.",
)
async def pair_device(
    body: DevicePairRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> DevicePairResponse:
    user_id = str(current_user.id)
    supabase = get_supabase()

    # Upsert into users table (device_id + omi_access_token columns)
    now = datetime.now(tz=timezone.utc).isoformat()
    supabase.table("users").update(
        {
            "omi_device_id": body.device_id,
            "omi_access_token": body.omi_access_token,
            "omi_paired_at": now,
        }
    ).eq("id", user_id).execute()

    return DevicePairResponse(
        user_id=uuid.UUID(user_id),
        device_id=body.device_id,
        paired=True,
        paired_at=now,
    )


@router.get(
    "/devices/{user_id}",
    response_model=DevicePairResponse,
    summary="Get Omi device pairing status",
)
async def get_device_status(
    user_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> DevicePairResponse:
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    supabase = get_supabase()
    result = supabase.table("users").select(
        "id, omi_device_id, omi_paired_at"
    ).eq("id", str(user_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = result.data
    device_id = data.get("omi_device_id") or ""
    return DevicePairResponse(
        user_id=user_id,
        device_id=device_id,
        paired=bool(device_id),
        paired_at=data.get("omi_paired_at"),
    )


@router.patch(
    "/devices/{user_id}",
    response_model=DevicePairResponse,
    summary="Re-pair Omi device (update access token)",
)
async def update_device_token(
    user_id: uuid.UUID,
    body: DeviceUpdateRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> DevicePairResponse:
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    supabase = get_supabase()
    now = datetime.now(tz=timezone.utc).isoformat()

    supabase.table("users").update(
        {
            "omi_access_token": body.omi_access_token,
            "omi_paired_at": now,
        }
    ).eq("id", str(user_id)).execute()

    # Fetch updated device_id
    result = supabase.table("users").select("omi_device_id").eq(
        "id", str(user_id)
    ).single().execute()

    device_id = result.data.get("omi_device_id", "") if result.data else ""
    return DevicePairResponse(
        user_id=user_id,
        device_id=device_id or "",
        paired=True,
        paired_at=now,
    )


@router.delete(
    "/devices/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unpair Omi device",
)
async def unpair_device(
    user_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> None:
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    supabase = get_supabase()
    supabase.table("users").update(
        {
            "omi_device_id": None,
            "omi_access_token": None,
            "omi_paired_at": None,
        }
    ).eq("id", str(user_id)).execute()


@router.get(
    "/sync/status/{user_id}",
    response_model=SyncStatusResponse,
    summary="Get Omi sync status for a user",
)
async def get_sync_status(
    user_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> SyncStatusResponse:
    if str(current_user.id) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    supabase = get_supabase()

    # Get user sync settings
    user_result = supabase.table("users").select(
        "omi_last_sync_at, sync_enabled"
    ).eq("id", str(user_id)).single().execute()

    user_data = user_result.data or {}

    # Count total recordings
    total_result = supabase.table("recordings").select(
        "id", count="exact"
    ).eq("user_id", str(user_id)).execute()
    recordings_count = total_result.count or 0

    # Count pending uploads
    pending_result = supabase.table("recordings").select(
        "id", count="exact"
    ).eq("user_id", str(user_id)).in_(
        "processing_status", ["pending", "queued"]
    ).execute()
    pending_uploads = pending_result.count or 0

    return SyncStatusResponse(
        user_id=user_id,
        last_sync_at=user_data.get("omi_last_sync_at"),
        recordings_count=recordings_count,
        pending_uploads=pending_uploads,
        sync_enabled=user_data.get("sync_enabled", True),
    )
