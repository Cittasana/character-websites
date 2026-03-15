"""
POST /api/upload/photos — photo upload endpoint.
Requirements:
- JWT authentication required
- JPEG/PNG/WebP only (magic bytes validation)
- Max 10MB per photo
- Stores in Supabase Storage (user-photos bucket), extracts dimensions, logs audit event
"""
import io
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.file_validation import get_image_dimensions, validate_photo_file
from app.storage import get_storage_service
from app.supabase_client import get_supabase

settings = get_settings()
router = APIRouter(prefix="/api/upload", tags=["upload"])
limiter = Limiter(key_func=get_remote_address)


class PhotoUploadItem(BaseModel):
    photo_id: uuid.UUID
    storage_path: str
    original_filename: str
    file_size_bytes: int
    detected_mime: str
    width_px: int | None
    height_px: int | None


class PhotoUploadResponse(BaseModel):
    uploaded: List[PhotoUploadItem]
    message: str


@router.post(
    "/photos",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload profile/portfolio photos",
    description=(
        "Upload 1-5 photos (JPEG/PNG/WebP). Max 10MB each. "
        "File types validated server-side via magic bytes."
    ),
)
@limiter.limit(settings.RATE_LIMIT_UPLOADS)
async def upload_photos(
    request: Request,
    files: Annotated[
        List[UploadFile],
        File(description="Image files: JPEG, PNG, or WebP"),
    ],
    current_user: Annotated[dict, Depends(get_current_active_user)],
    photo_type: str = "profile",
) -> PhotoUploadResponse:
    user_id = str(current_user.id)

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 photos per request",
        )

    supabase = get_supabase()
    storage = get_storage_service()
    uploaded_items: List[PhotoUploadItem] = []

    for file in files:
        file_data = await file.read()
        file_size = len(file_data)
        original_filename = file.filename or "photo.jpg"

        # Validate magic bytes
        validation = validate_photo_file(file_data, file_size)
        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{original_filename}': {validation.error}",
            )

        # Extract dimensions
        dims = get_image_dimensions(file_data)
        width_px, height_px = dims if dims else (None, None)

        # Upload to Supabase Storage
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        try:
            storage_path = storage.upload_photo(
                user_id=user_id,
                filename=unique_filename,
                file_bytes=file_data,
                content_type=validation.detected_mime,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage upload failed for '{original_filename}': {exc}",
            )

        # Persist photo row
        try:
            result = supabase.table("photos").insert(
                {
                    "user_id": user_id,
                    "storage_path": storage_path,
                    "storage_bucket": "user-photos",
                    "original_filename": original_filename,
                    "file_size_bytes": file_size,
                    "mime_type": validation.detected_mime,
                    "width_px": width_px,
                    "height_px": height_px,
                    "photo_type": photo_type,
                }
            ).execute()
            photo_id = result.data[0]["id"]
        except Exception as exc:
            try:
                storage.delete_file("user-photos", storage_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database insert failed: {exc}",
            )

        # Audit log
        try:
            supabase.table("audit_logs").insert(
                {
                    "user_id": user_id,
                    "event_type": "upload.photo",
                    "resource_type": "photo",
                    "resource_id": photo_id,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "request_path": str(request.url.path),
                    "request_method": "POST",
                    "response_status": 201,
                    "metadata": {
                        "file_size_bytes": file_size,
                        "mime_type": validation.detected_mime,
                        "storage_path": storage_path,
                        "dimensions": {"width": width_px, "height": height_px},
                    },
                }
            ).execute()
        except Exception:
            pass

        uploaded_items.append(
            PhotoUploadItem(
                photo_id=uuid.UUID(photo_id),
                storage_path=storage_path,
                original_filename=original_filename,
                file_size_bytes=file_size,
                detected_mime=validation.detected_mime,
                width_px=width_px,
                height_px=height_px,
            )
        )

    return PhotoUploadResponse(
        uploaded=uploaded_items,
        message=f"{len(uploaded_items)} photo(s) uploaded successfully.",
    )
