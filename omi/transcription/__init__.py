"""Whisper transcription fallback for Omi recordings without transcripts."""
from .whisper_fallback import WhisperTranscriber, TranscriptionResult

__all__ = ["WhisperTranscriber", "TranscriptionResult"]
