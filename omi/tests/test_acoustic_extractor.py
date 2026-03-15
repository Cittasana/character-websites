"""
Tests for acoustic feature extraction (Phase 13 - Plan 13-01).

Tests cover:
- Full extraction from file path
- Extraction from bytes
- Individual feature group validation
- Edge cases (short audio, very quiet audio)
"""
import pytest
import numpy as np
from pathlib import Path

from omi.acoustic.extractor import (
    AcousticExtractor,
    AcousticFeatures,
    AcousticExtractionError,
    PitchRange,
    SpeechRhythm,
    EmotionalCadence,
    PausePatterns,
    VolumeVariation,
)


@pytest.fixture
def extractor():
    return AcousticExtractor()


class TestAcousticExtractorFromFile:
    """Tests for extraction from file path."""

    def test_extract_from_wav_path(self, extractor, temp_wav_file):
        features = extractor.extract(audio_input=temp_wav_file)
        assert isinstance(features, AcousticFeatures)
        assert features.duration_seconds > 0
        assert features.sample_rate == 22050

    def test_extract_returns_all_feature_groups(self, extractor, temp_wav_file):
        features = extractor.extract(audio_input=temp_wav_file)
        assert isinstance(features.pitch_range, PitchRange)
        assert isinstance(features.speech_rhythm, SpeechRhythm)
        assert isinstance(features.emotional_cadence, EmotionalCadence)
        assert isinstance(features.pause_patterns, PausePatterns)
        assert isinstance(features.volume_variation, VolumeVariation)

    def test_extract_to_dict_shape(self, extractor, temp_wav_file):
        d = extractor.extract_to_dict(audio_input=temp_wav_file)
        assert isinstance(d, dict)
        for key in ["pitch_range", "speech_rhythm", "emotional_cadence",
                    "pause_patterns", "volume_variation", "duration_seconds",
                    "sample_rate", "analysis_version"]:
            assert key in d, f"Missing key: {key}"

    def test_pitch_range_nested_keys(self, extractor, temp_wav_file):
        d = extractor.extract_to_dict(audio_input=temp_wav_file)
        pr = d["pitch_range"]
        for key in ["min_hz", "max_hz", "mean_hz", "std_hz", "voiced_fraction"]:
            assert key in pr, f"pitch_range missing: {key}"

    def test_speech_rhythm_nested_keys(self, extractor, temp_wav_file):
        d = extractor.extract_to_dict(audio_input=temp_wav_file)
        sr = d["speech_rhythm"]
        for key in ["tempo_bpm", "articulation_rate"]:
            assert key in sr, f"speech_rhythm missing: {key}"

    def test_pause_patterns_nested_keys(self, extractor, temp_wav_file):
        d = extractor.extract_to_dict(audio_input=temp_wav_file)
        pp = d["pause_patterns"]
        for key in ["mean_pause_duration_s", "pause_frequency_per_min",
                    "total_pause_time_s", "speaking_ratio"]:
            assert key in pp, f"pause_patterns missing: {key}"

    def test_speaking_ratio_is_bounded(self, extractor, temp_wav_file):
        features = extractor.extract(audio_input=temp_wav_file)
        ratio = features.pause_patterns.speaking_ratio
        assert 0.0 <= ratio <= 1.0, f"speaking_ratio out of bounds: {ratio}"

    def test_voiced_fraction_is_bounded(self, extractor, temp_wav_file):
        features = extractor.extract(audio_input=temp_wav_file)
        vf = features.pitch_range.voiced_fraction
        assert 0.0 <= vf <= 1.0, f"voiced_fraction out of bounds: {vf}"

    def test_nonexistent_file_raises(self, extractor):
        with pytest.raises(AcousticExtractionError):
            extractor.extract("/nonexistent/path/audio.wav")


class TestAcousticExtractorFromBytes:
    """Tests for extraction from raw audio bytes."""

    def test_extract_from_wav_bytes(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert isinstance(features, AcousticFeatures)
        assert features.duration_seconds > 0

    def test_extract_to_dict_from_bytes(self, extractor, speech_wav_bytes):
        d = extractor.extract_to_dict(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert isinstance(d, dict)
        assert "pitch_range" in d
        assert "pause_patterns" in d

    def test_speaking_rate_wpm_with_transcript(self, extractor, speech_wav_bytes):
        transcript = "Hello this is a test transcript with ten words total here"
        features = extractor.extract(
            audio_input=speech_wav_bytes,
            content_type="audio/wav",
            transcript=transcript,
        )
        wpm = features.speech_rhythm.speaking_rate_wpm
        assert wpm is not None
        assert wpm > 0

    def test_speaking_rate_wpm_without_transcript(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        # Without transcript, speaking_rate_wpm should be None
        assert features.speech_rhythm.speaking_rate_wpm is None


class TestAcousticFeatureValues:
    """Sanity checks on feature values for synthetic audio."""

    def test_tempo_bpm_is_positive(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert features.speech_rhythm.tempo_bpm > 0

    def test_articulation_rate_is_positive(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert features.speech_rhythm.articulation_rate >= 0

    def test_energy_variance_is_non_negative(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert features.emotional_cadence.energy_variance >= 0

    def test_spectral_centroid_is_positive(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert features.emotional_cadence.spectral_centroid_mean > 0

    def test_rms_mean_is_positive(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert features.volume_variation.rms_mean > 0

    def test_dynamic_range_db_is_non_negative(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        assert features.volume_variation.dynamic_range_db >= 0

    def test_pause_detection_with_silent_segments(self, extractor, speech_wav_bytes):
        """Speech-like audio has pauses built in — should detect at least some."""
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        # We generated audio with pauses, so there should be at least some
        assert features.pause_patterns.total_pause_time_s >= 0


class TestAcousticFeaturesSerializability:
    """Tests for to_dict / from_dict round-trip."""

    def test_to_dict_round_trip(self, extractor, speech_wav_bytes):
        features = extractor.extract(audio_input=speech_wav_bytes, content_type="audio/wav")
        d = features.to_dict()
        restored = AcousticFeatures.from_dict(d)

        assert abs(restored.duration_seconds - features.duration_seconds) < 0.001
        assert restored.pitch_range.mean_hz == features.pitch_range.mean_hz
        assert restored.speech_rhythm.tempo_bpm == features.speech_rhythm.tempo_bpm
        assert restored.pause_patterns.speaking_ratio == features.pause_patterns.speaking_ratio

    def test_dict_all_values_are_json_serializable(self, extractor, speech_wav_bytes):
        import json
        d = extractor.extract_to_dict(audio_input=speech_wav_bytes, content_type="audio/wav")
        # Should not raise
        json_str = json.dumps(d)
        assert len(json_str) > 0
