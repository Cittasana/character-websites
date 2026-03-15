"""
Shared test fixtures for the Omi integration tests.

Generates real test audio using numpy/scipy (or librosa) to avoid
needing external audio files. All tests that need audio use these fixtures.
"""
import io
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

# ── Audio generation helpers ──────────────────────────────────────────────────

def _generate_sine_wave(
    frequency: float = 220.0,
    duration: float = 3.0,
    sample_rate: int = 22050,
    amplitude: float = 0.3,
) -> np.ndarray:
    """Generate a pure sine wave (simulates a voice tone)."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)


def _generate_speech_like_audio(
    duration: float = 5.0,
    sample_rate: int = 22050,
) -> np.ndarray:
    """
    Generate speech-like audio: mix of harmonics, amplitude modulation, pauses.
    More realistic for acoustic feature testing than pure sine.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Fundamental at 150 Hz (male voice range) with harmonics
    fundamental = 150.0
    audio = np.zeros_like(t)
    for harmonic in [1, 2, 3, 4, 5]:
        amplitude = 0.2 / harmonic
        audio += amplitude * np.sin(2 * np.pi * fundamental * harmonic * t)

    # Amplitude modulation (simulates syllable rhythm ~4 Hz)
    am_freq = 4.0
    am = 0.5 + 0.5 * np.sin(2 * np.pi * am_freq * t)
    audio = audio * am

    # Add pauses (zero out every ~1.5 seconds for 0.3 seconds)
    pause_interval = int(sample_rate * 1.5)
    pause_duration = int(sample_rate * 0.3)
    for i in range(0, len(audio) - pause_duration, pause_interval):
        audio[i:i + pause_duration] = 0.0

    # Add light noise
    noise = np.random.normal(0, 0.005, len(audio))
    audio = (audio + noise).astype(np.float32)

    # Normalize
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.8

    return audio


def _audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = 22050) -> bytes:
    """Convert numpy float32 array to WAV bytes."""
    import struct
    import wave

    # Convert float32 to int16
    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def sample_rate():
    return 22050


@pytest.fixture(scope="session")
def sine_audio_array(sample_rate):
    """Simple 3-second sine wave numpy array."""
    return _generate_sine_wave(frequency=220.0, duration=3.0, sample_rate=sample_rate)


@pytest.fixture(scope="session")
def speech_audio_array(sample_rate):
    """Speech-like 5-second audio numpy array."""
    return _generate_speech_like_audio(duration=5.0, sample_rate=sample_rate)


@pytest.fixture(scope="session")
def sine_wav_bytes(sine_audio_array, sample_rate):
    """Simple sine wave as WAV bytes."""
    return _audio_to_wav_bytes(sine_audio_array, sample_rate)


@pytest.fixture(scope="session")
def speech_wav_bytes(speech_audio_array, sample_rate):
    """Speech-like audio as WAV bytes."""
    return _audio_to_wav_bytes(speech_audio_array, sample_rate)


@pytest.fixture
def temp_wav_file(speech_wav_bytes):
    """Write speech WAV to a temp file, yield path, then clean up."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(speech_wav_bytes)
        tmp_path = f.name
    yield Path(tmp_path)
    Path(tmp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_dir(tmp_path):
    """A temporary directory for test file artifacts."""
    return tmp_path


@pytest.fixture
def mock_user_id():
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def mock_user_jwt():
    return "eyJhbGciOiJIUzI1NiJ9.mock.signature"


@pytest.fixture
def mock_omi_access_token():
    return "omi-access-token-mock-12345"


@pytest.fixture
def fernet_key():
    """Generate a fresh Fernet key for each test."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key()
