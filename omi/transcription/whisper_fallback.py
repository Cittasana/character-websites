"""
Whisper transcription fallback.

Used when an Omi recording has no transcript (e.g. device was offline,
Omi cloud didn't process it, or the recording is too short for Omi's pipeline).

Two modes:
1. OpenAI Whisper API (WHISPER_USE_LOCAL=False, default):
   - Sends audio to openai.audio.transcriptions.create
   - Requires OPENAI_API_KEY
   - Supports language detection

2. Local openai-whisper (WHISPER_USE_LOCAL=True):
   - Runs inference locally using the `whisper` Python package
   - Slower but no API cost, no data leaves the machine
   - Install: pip install openai-whisper

Language detection:
  - From Whisper: detected language returned in response
  - Fallback: `langdetect` library if Whisper doesn't provide language
"""
import io
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from omi.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result of a Whisper transcription."""
    text: str
    language: Optional[str]     # ISO 639-1 code (e.g. 'en', 'de', 'fr')
    source: str                  # 'whisper_api' | 'whisper_local'
    confidence: Optional[float] = None  # 0.0-1.0 (API doesn't provide this; local might)
    duration_seconds: Optional[float] = None

    @property
    def is_empty(self) -> bool:
        return not self.text or not self.text.strip()


class WhisperTranscriber:
    """
    Transcribes audio using OpenAI Whisper (API or local).

    Usage:
        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(audio_bytes, content_type="audio/wav")
        if result and not result.is_empty:
            print(result.text, result.language)
    """

    def __init__(self):
        self.settings = get_settings()

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        hint_language: Optional[str] = None,
    ) -> Optional[TranscriptionResult]:
        """
        Transcribe audio bytes.

        Args:
            audio_bytes: Raw audio bytes (plaintext, not encrypted)
            content_type: MIME type of the audio
            hint_language: Language hint (ISO 639-1) to improve accuracy

        Returns:
            TranscriptionResult or None if transcription fails/not available
        """
        if self.settings.WHISPER_USE_LOCAL:
            return await self._transcribe_local(audio_bytes, content_type, hint_language)
        else:
            return await self._transcribe_api(audio_bytes, content_type, hint_language)

    async def _transcribe_api(
        self,
        audio_bytes: bytes,
        content_type: str,
        hint_language: Optional[str],
    ) -> Optional[TranscriptionResult]:
        """Transcribe via OpenAI Whisper API."""
        if not self.settings.OPENAI_API_KEY:
            logger.warning(
                "OPENAI_API_KEY not set — Whisper API transcription unavailable. "
                "Set OPENAI_API_KEY or enable WHISPER_USE_LOCAL=true"
            )
            return None

        try:
            from openai import AsyncOpenAI
        except ImportError:
            logger.error(
                "openai package not installed. Install: pip install openai"
            )
            return None

        client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)

        # Determine file extension from content-type
        ext = _content_type_to_ext(content_type)
        filename = f"audio{ext}"

        # Build the file tuple for the API
        audio_file = (filename, io.BytesIO(audio_bytes), content_type)

        logger.info(
            f"Transcribing {len(audio_bytes)} bytes via OpenAI Whisper API "
            f"(model={self.settings.WHISPER_MODEL}, lang={hint_language or 'auto'})"
        )

        try:
            kwargs: dict = {
                "model": self.settings.WHISPER_MODEL,
                "file": audio_file,
                "response_format": "verbose_json",  # includes language
            }
            if hint_language:
                kwargs["language"] = hint_language

            response = await client.audio.transcriptions.create(**kwargs)

            text = response.text or ""
            language = getattr(response, "language", None)
            duration = getattr(response, "duration", None)

            logger.info(
                f"Whisper API transcription complete: {len(text)} chars, "
                f"language={language}, duration={duration}s"
            )

            return TranscriptionResult(
                text=text.strip(),
                language=language,
                source="whisper_api",
                duration_seconds=duration,
            )

        except Exception as exc:
            logger.error(f"Whisper API transcription failed: {exc}")
            return None

    async def _transcribe_local(
        self,
        audio_bytes: bytes,
        content_type: str,
        hint_language: Optional[str],
    ) -> Optional[TranscriptionResult]:
        """Transcribe using local openai-whisper model."""
        try:
            import whisper
        except ImportError:
            logger.error(
                "openai-whisper not installed. Install: pip install openai-whisper"
            )
            return None

        import asyncio
        import functools

        logger.info(
            f"Transcribing {len(audio_bytes)} bytes locally "
            f"(model={self.settings.WHISPER_LOCAL_MODEL})"
        )

        # Write audio to a temp file (whisper needs a file path)
        ext = _content_type_to_ext(content_type)
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Run in executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                functools.partial(
                    _run_whisper_local,
                    tmp_path,
                    self.settings.WHISPER_LOCAL_MODEL,
                    hint_language,
                ),
            )
            return result
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text using langdetect.
        Returns ISO 639-1 code or None if detection fails.
        """
        try:
            from langdetect import detect, LangDetectException
            return detect(text)
        except ImportError:
            logger.debug("langdetect not installed — language detection unavailable")
            return None
        except Exception as exc:
            logger.debug(f"Language detection failed: {exc}")
            return None


def _run_whisper_local(
    audio_path: str,
    model_size: str,
    hint_language: Optional[str],
) -> Optional[TranscriptionResult]:
    """
    Run local whisper in a thread (CPU-bound operation).
    Called via loop.run_in_executor.
    """
    try:
        import whisper

        model = whisper.load_model(model_size)

        kwargs: dict = {"verbose": False}
        if hint_language:
            kwargs["language"] = hint_language

        result = model.transcribe(audio_path, **kwargs)

        text = result.get("text", "").strip()
        language = result.get("language")
        duration = result.get("duration")

        logger.info(
            f"Local whisper transcription complete: {len(text)} chars, "
            f"language={language}"
        )

        return TranscriptionResult(
            text=text,
            language=language,
            source="whisper_local",
            duration_seconds=duration,
        )
    except Exception as exc:
        logger.error(f"Local whisper transcription failed: {exc}")
        return None


def _content_type_to_ext(content_type: str) -> str:
    """Convert MIME type to file extension for Whisper."""
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/wave": ".wav",
        "audio/m4a": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/mp4": ".mp4",
        "audio/ogg": ".ogg",
        "audio/opus": ".opus",
        "audio/webm": ".webm",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
    }
    base = content_type.split(";")[0].strip().lower()
    return mapping.get(base, ".wav")
