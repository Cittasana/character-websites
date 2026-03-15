"""
Acoustic metadata extraction using librosa.
Extracts: pitch range/avg, speech rhythm/pacing, pause patterns, volume variations.
"""
import io
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def extract_acoustic_metadata(audio_data: bytes, sample_rate: int = 22050) -> dict[str, Any]:
    """
    Extract acoustic features from raw audio bytes.
    Returns a dict of acoustic metadata suitable for storing in the DB
    and passing to the Claude personality analysis.

    Features extracted:
    - pitch_hz: fundamental frequency stats (min, max, mean, std)
    - speech_rhythm: syllable-level timing metrics
    - pacing_wpm: estimated words per minute
    - pause_patterns: silence detection stats
    - volume_variations: RMS energy stats
    - spectral_features: brightness, rolloff
    """
    try:
        import librosa
        import soundfile as sf
    except ImportError as e:
        logger.error("librosa/soundfile not available: %s", e)
        return {"error": "Audio analysis library not available"}

    try:
        # Load audio from bytes
        audio_buffer = io.BytesIO(audio_data)
        y, sr = librosa.load(audio_buffer, sr=sample_rate, mono=True)

        duration_seconds = float(librosa.get_duration(y=y, sr=sr))

        # ── Pitch Analysis ────────────────────────────────────────────────
        # Use pyin for robust pitch tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
        )

        voiced_f0 = f0[voiced_flag] if voiced_flag is not None else np.array([])
        pitch_stats: dict[str, float | None]
        if len(voiced_f0) > 0:
            pitch_stats = {
                "min_hz": float(np.min(voiced_f0)),
                "max_hz": float(np.max(voiced_f0)),
                "mean_hz": float(np.mean(voiced_f0)),
                "std_hz": float(np.std(voiced_f0)),
                "range_hz": float(np.max(voiced_f0) - np.min(voiced_f0)),
                "voiced_ratio": float(np.mean(voiced_probs)) if voiced_probs is not None else None,
            }
        else:
            pitch_stats = {
                "min_hz": None, "max_hz": None, "mean_hz": None,
                "std_hz": None, "range_hz": None, "voiced_ratio": 0.0,
            }

        # ── Volume / RMS Energy ───────────────────────────────────────────
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)

        volume_stats = {
            "mean_db": float(np.mean(rms_db)),
            "std_db": float(np.std(rms_db)),
            "min_db": float(np.min(rms_db)),
            "max_db": float(np.max(rms_db)),
            "dynamic_range_db": float(np.max(rms_db) - np.min(rms_db)),
        }

        # ── Pause Detection ───────────────────────────────────────────────
        # Detect non-silent intervals using top_db threshold
        non_silent_intervals = librosa.effects.split(y, top_db=35)

        total_speech_duration = sum(
            (end - start) / sr for start, end in non_silent_intervals
        )
        total_pause_duration = duration_seconds - total_speech_duration
        pause_count = max(0, len(non_silent_intervals) - 1)

        pause_durations = []
        for i in range(1, len(non_silent_intervals)):
            pause_start = non_silent_intervals[i - 1][1] / sr
            pause_end = non_silent_intervals[i][0] / sr
            pause_dur = pause_end - pause_start
            if pause_dur > 0.1:  # ignore sub-100ms gaps
                pause_durations.append(pause_dur)

        pause_stats = {
            "total_pause_duration_s": float(total_pause_duration),
            "total_speech_duration_s": float(total_speech_duration),
            "speech_ratio": float(total_speech_duration / duration_seconds)
            if duration_seconds > 0 else 0.0,
            "pause_count": int(pause_count),
            "mean_pause_duration_s": float(np.mean(pause_durations)) if pause_durations else 0.0,
            "max_pause_duration_s": float(np.max(pause_durations)) if pause_durations else 0.0,
        }

        # ── Speech Rate / Pacing ──────────────────────────────────────────
        # Estimate syllable rate using onset detection as a proxy
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
        # Rough estimate: 1.5 syllables per onset on average in natural speech
        estimated_syllables = len(onsets) * 1.5
        # Average: ~1.5 syllables per word in English
        estimated_words = estimated_syllables / 1.5
        pacing_wpm = (estimated_words / duration_seconds * 60) if duration_seconds > 0 else 0

        pacing_stats = {
            "onset_rate_per_sec": float(len(onsets) / duration_seconds) if duration_seconds > 0 else 0.0,
            "estimated_wpm": float(pacing_wpm),
            "duration_seconds": float(duration_seconds),
        }

        # ── Spectral Features ─────────────────────────────────────────────
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]

        spectral_stats = {
            "centroid_mean_hz": float(np.mean(spectral_centroid)),
            "centroid_std_hz": float(np.std(spectral_centroid)),
            "rolloff_mean_hz": float(np.mean(spectral_rolloff)),
            "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
        }

        return {
            "duration_seconds": float(duration_seconds),
            "pitch": pitch_stats,
            "volume": volume_stats,
            "pauses": pause_stats,
            "pacing": pacing_stats,
            "spectral": spectral_stats,
        }

    except Exception as exc:
        logger.error("Acoustic extraction failed: %s", exc, exc_info=True)
        return {"error": str(exc), "duration_seconds": None}


def format_acoustic_for_claude(metadata: dict[str, Any]) -> str:
    """
    Format extracted acoustic metadata into a human-readable summary
    suitable for inclusion in a Claude prompt.
    """
    if "error" in metadata:
        return f"[Acoustic analysis unavailable: {metadata['error']}]"

    pitch = metadata.get("pitch", {})
    volume = metadata.get("volume", {})
    pauses = metadata.get("pauses", {})
    pacing = metadata.get("pacing", {})

    lines = [
        "=== Acoustic Voice Analysis ===",
        f"Duration: {metadata.get('duration_seconds', 'N/A'):.1f}s",
        "",
        "Pitch Profile:",
        f"  Range: {pitch.get('min_hz', 'N/A'):.0f}–{pitch.get('max_hz', 'N/A'):.0f} Hz"
        if pitch.get("min_hz") else "  Range: N/A",
        f"  Mean: {pitch.get('mean_hz', 'N/A'):.0f} Hz"
        if pitch.get("mean_hz") else "  Mean: N/A",
        f"  Variability (std): {pitch.get('std_hz', 'N/A'):.1f} Hz"
        if pitch.get("std_hz") else "  Variability: N/A",
        "",
        "Pacing & Rhythm:",
        f"  Estimated WPM: {pacing.get('estimated_wpm', 'N/A'):.0f}",
        f"  Onset rate: {pacing.get('onset_rate_per_sec', 'N/A'):.2f}/sec",
        "",
        "Pause Patterns:",
        f"  Speech ratio: {pauses.get('speech_ratio', 0) * 100:.0f}%",
        f"  Pause count: {pauses.get('pause_count', 'N/A')}",
        f"  Mean pause: {pauses.get('mean_pause_duration_s', 'N/A'):.2f}s",
        "",
        "Volume/Energy:",
        f"  Mean level: {volume.get('mean_db', 'N/A'):.1f} dB",
        f"  Dynamic range: {volume.get('dynamic_range_db', 'N/A'):.1f} dB",
        f"  Variation (std): {volume.get('std_db', 'N/A'):.1f} dB",
    ]

    return "\n".join(lines)
