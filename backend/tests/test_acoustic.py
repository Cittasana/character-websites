"""
Unit tests for acoustic metadata extraction.
Uses synthetic audio data to avoid requiring actual audio files.
"""
import numpy as np
import pytest

from app.analysis.acoustic import format_acoustic_for_claude


class TestFormatAcousticForClaude:
    def test_formats_complete_metadata(self) -> None:
        metadata = {
            "duration_seconds": 45.3,
            "pitch": {
                "min_hz": 85.0,
                "max_hz": 250.0,
                "mean_hz": 140.0,
                "std_hz": 35.0,
                "range_hz": 165.0,
                "voiced_ratio": 0.75,
            },
            "volume": {
                "mean_db": -20.0,
                "std_db": 5.0,
                "min_db": -40.0,
                "max_db": -5.0,
                "dynamic_range_db": 35.0,
            },
            "pauses": {
                "total_pause_duration_s": 10.0,
                "total_speech_duration_s": 35.3,
                "speech_ratio": 0.78,
                "pause_count": 8,
                "mean_pause_duration_s": 1.25,
                "max_pause_duration_s": 3.5,
            },
            "pacing": {
                "onset_rate_per_sec": 4.2,
                "estimated_wpm": 145.0,
                "duration_seconds": 45.3,
            },
            "spectral": {
                "centroid_mean_hz": 1500.0,
                "centroid_std_hz": 300.0,
                "rolloff_mean_hz": 3000.0,
                "zero_crossing_rate_mean": 0.05,
            },
        }

        result = format_acoustic_for_claude(metadata)
        assert "45.3s" in result
        assert "85" in result  # min pitch
        assert "250" in result  # max pitch
        assert "145" in result  # WPM
        assert "78%" in result  # speech ratio

    def test_handles_error_metadata(self) -> None:
        metadata = {"error": "Audio file corrupt", "duration_seconds": None}
        result = format_acoustic_for_claude(metadata)
        assert "unavailable" in result.lower()
        assert "Audio file corrupt" in result

    def test_handles_none_pitch_values(self) -> None:
        metadata = {
            "duration_seconds": 10.0,
            "pitch": {
                "min_hz": None,
                "max_hz": None,
                "mean_hz": None,
                "std_hz": None,
                "range_hz": None,
                "voiced_ratio": 0.0,
            },
            "volume": {"mean_db": -30.0, "std_db": 3.0, "min_db": -50.0,
                       "max_db": -10.0, "dynamic_range_db": 40.0},
            "pauses": {"total_pause_duration_s": 2.0, "total_speech_duration_s": 8.0,
                       "speech_ratio": 0.8, "pause_count": 3,
                       "mean_pause_duration_s": 0.67, "max_pause_duration_s": 1.0},
            "pacing": {"onset_rate_per_sec": 3.0, "estimated_wpm": 120.0, "duration_seconds": 10.0},
            "spectral": {},
        }
        # Should not raise
        result = format_acoustic_for_claude(metadata)
        assert isinstance(result, str)
        assert len(result) > 0
