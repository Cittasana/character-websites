"""
POST /api/upload/photos — photo upload endpoint.
Requirements:
- JWT authentication required
- JPEG/PNG/WebP only (magic bytes validation)
- Max 10MB per photo
- Stores in S3, extracts dimensions, logs audit event
"""
import io
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.database import get_db
from app.file_validation import get_image_dimensions, validate_photo_file
from app.models.audit_log import AuditLog
from app.models.photo import Photo
from app.models.user import User
from app.storage import upload_file_to_s3
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()
router = APIRouter(prefix="/api/upload", tags=["upload"])
limiter = Limiter(key_func=get_remote_address)


class PhotoUploadItem(BaseModel):
    photo_id: uuid.UUID
    s3_key: str
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
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    photo_type: str = "profile",
) -> PhotoUploadResponse:
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

    uploaded_items: List[PhotoUploadItem] = []

    for file in files:
        file_data = await file.read()
        file_size = len(file_data)

        # Validate magic bytes
        validation = validate_photo_file(file_data, file_size)
        if not validation.valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}': {validation.error}",
            )

        # Extract dimensions
        dims = get_image_dimensions(file_data)
        width_px, height_px = dims if dims else (None, None)

        # Upload to S3
        s3_result = upload_file_to_s3(
            file_obj=io.BytesIO(file_data),
            user_id=str(current_user.id),
            file_type="photo",
            original_filename=file.filename or "photo.jpg",
            content_type=validation.detected_mime,
        )

        # Persist photo row
        photo = Photo(
            user_id=current_user.id,
            s3_key=s3_result["s3_key"],
            s3_bucket=s3_result["s3_bucket"],
            original_filename=file.filename or "photo.jpg",
            file_size_bytes=file_size,
            mime_type=validation.detected_mime,
            width_px=width_px,
            height_px=height_px,
            photo_type=photo_type,
        )
        db.add(photo)
        await db.flush()

        # Audit log
        log = AuditLog(
            user_id=current_user.id,
            event_type="upload.photo",
            resource_type="photo",
            resource_id=str(photo.id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_path=str(request.url.path),
            request_method="POST",
            response_status=201,
            metadata={
                "file_size_bytes": file_size,
                "mime_type": validation.detected_mime,
                "s3_key": s3_result["s3_key"],
                "dimensions": {"width": width_px, "height": height_px},
            },
        )
        db.add(log)

        uploaded_items.append(
            PhotoUploadItem(
                photo_id=photo.id,
                s3_key=s3_result["s3_key"],
                original_filename=photo.original_filename,
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
