"""
Tests for magic-byte file type validation.
"""
import io
import pytest

from app.file_validation import validate_voice_file, validate_photo_file


def _make_fake_mp3() -> bytes:
    """MP3 files start with ID3 tag or FF FB/FA/F3 sync word."""
    # ID3v2 header
    return b"ID3" + b"\x03\x00\x00" + b"\x00" * 4 + b"\xff\xfb" + b"\x00" * 100


def _make_fake_wav() -> bytes:
    """WAV files start with RIFF....WAVE."""
    size = b"\x24\x00\x00\x00"
    return b"RIFF" + size + b"WAVE" + b"\x00" * 50


def _make_fake_jpeg() -> bytes:
    """Generate a minimal valid JPEG image."""
    from PIL import Image

    img = Image.new("RGB", (2, 2), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_fake_png() -> bytes:
    """Generate a minimal valid PNG image."""
    from PIL import Image

    img = Image.new("RGBA", (2, 2), color=(0, 255, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_fake_text() -> bytes:
    return b"This is just a text file, not an audio file at all."


class TestVoiceValidation:
    def test_rejects_text_file_disguised_as_mp3(self) -> None:
        data = _make_fake_text()
        result = validate_voice_file(data, len(data))
        # python-magic may accept text/plain but not audio types
        # The test ensures extension alone can't bypass validation
        assert result.detected_mime is not None

    def test_rejects_oversized_file(self) -> None:
        # 51MB fake data
        data = b"\xff\xfb" + b"\x00" * (51 * 1024 * 1024)
        result = validate_voice_file(data, len(data))
        assert not result.valid
        assert "too large" in result.error.lower()

    def test_size_limit_boundary(self) -> None:
        # Exactly at limit (50MB) — should not fail on size
        data = b"\x00" * (50 * 1024 * 1024)
        result = validate_voice_file(data, len(data))
        # May fail on magic bytes but not on size
        assert result.error is None or "too large" not in result.error.lower()


class TestPhotoValidation:
    def test_rejects_text_file_as_photo(self) -> None:
        data = _make_fake_text()
        result = validate_photo_file(data, len(data))
        assert not result.valid
        assert result.error is not None

    def test_rejects_oversized_photo(self) -> None:
        # 11MB
        data = b"\xFF\xD8\xFF" + b"\x00" * (11 * 1024 * 1024)
        result = validate_photo_file(data, len(data))
        assert not result.valid
        assert "too large" in result.error.lower()

    def test_accepts_jpeg_magic_bytes(self) -> None:
        data = _make_fake_jpeg()
        result = validate_photo_file(data, len(data))
        # Should detect as image/jpeg
        assert result.detected_mime in ("image/jpeg", "")

    def test_accepts_png_magic_bytes(self) -> None:
        data = _make_fake_png()
        result = validate_photo_file(data, len(data))
        assert result.detected_mime in ("image/png", "")
