"""
Server-side file type validation using magic bytes (not just file extension).
This is the authoritative validator — extension alone is NOT sufficient.
"""
import io
from typing import NamedTuple

import magic  # python-magic, wraps libmagic

from app.config import get_settings

settings = get_settings()


class ValidationResult(NamedTuple):
    valid: bool
    detected_mime: str
    error: str | None = None


# ── Magic byte signatures ─────────────────────────────────────────────────────
# These are the MIME types libmagic will detect for allowed file formats.
_VOICE_MIME_TYPES: frozenset[str] = frozenset({
    "audio/mpeg",       # MP3
    "audio/mp3",        # MP3 (alternate)
    "audio/wav",        # WAV
    "audio/x-wav",      # WAV (alternate)
    "audio/wave",       # WAV (alternate)
    "audio/x-m4a",      # M4A
    "audio/mp4",        # M4A / MP4 audio
    "video/mp4",        # Some M4A files are detected as video/mp4
})

_PHOTO_MIME_TYPES: frozenset[str] = frozenset({
    "image/jpeg",       # JPEG/JPG
    "image/png",        # PNG
    "image/webp",       # WebP
})


def _detect_mime(data: bytes) -> str:
    """Detect MIME type from the first 8KB of file data using libmagic."""
    return magic.from_buffer(data[:8192], mime=True)


def validate_voice_file(data: bytes, size_bytes: int) -> ValidationResult:
    """
    Validate audio file:
    - Magic bytes must match allowed audio types
    - Size must not exceed VOICE_MAX_SIZE_MB
    """
    max_bytes = settings.voice_max_bytes
    if size_bytes > max_bytes:
        return ValidationResult(
            valid=False,
            detected_mime="",
            error=f"File too large: {size_bytes} bytes (max {max_bytes} bytes / {settings.VOICE_MAX_SIZE_MB}MB)",
        )

    detected = _detect_mime(data)
    if detected not in _VOICE_MIME_TYPES:
        return ValidationResult(
            valid=False,
            detected_mime=detected,
            error=f"Invalid file type: detected '{detected}'. Allowed: mp3, wav, m4a",
        )

    return ValidationResult(valid=True, detected_mime=detected)


def validate_photo_file(data: bytes, size_bytes: int) -> ValidationResult:
    """
    Validate photo file:
    - Magic bytes must match allowed image types
    - Size must not exceed PHOTO_MAX_SIZE_MB
    """
    max_bytes = settings.photo_max_bytes
    if size_bytes > max_bytes:
        return ValidationResult(
            valid=False,
            detected_mime="",
            error=f"File too large: {size_bytes} bytes (max {max_bytes} bytes / {settings.PHOTO_MAX_SIZE_MB}MB)",
        )

    detected = _detect_mime(data)
    if detected not in _PHOTO_MIME_TYPES:
        return ValidationResult(
            valid=False,
            detected_mime=detected,
            error=f"Invalid file type: detected '{detected}'. Allowed: JPEG, PNG, WebP",
        )

    return ValidationResult(valid=True, detected_mime=detected)


def get_image_dimensions(data: bytes) -> tuple[int, int] | None:
    """
    Extract image dimensions from raw bytes using Pillow.
    Returns (width, height) or None if extraction fails.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        return img.size  # (width, height)
    except Exception:
        return None
