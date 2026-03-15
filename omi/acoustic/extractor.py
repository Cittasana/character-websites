"""
Acoustic feature extraction using librosa.

Extracts personality-relevant acoustic signals from voice recordings:

Feature groups and their personality correlations:
  - pitch_range: min/max/mean Hz → emotional range, confidence
  - speech_rhythm: tempo BPM, articulation rate → introversion/extroversion
  - emotional_cadence: energy envelope variance, spectral centroid variance → warmth/enthusiasm
  - pause_patterns: mean pause duration, pause frequency per minute → thoughtfulness
  - volume_variation: RMS energy std dev → confidence and energy indicators

Output: dict matching the `acoustic_metadata` field in the backend `recordings` table.
This dict is passed alongside the transcript in the Celery job payload when Claude
performs personality analysis.

Field names are fixed — the Backend Celery worker (Phase 3) reads these exact keys.
"""
import logging
import tempfile
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Librosa analysis constants
SAMPLE_RATE = 22050                 # Hz — librosa default, sufficient for voice
HOP_LENGTH = 512                    # frames
N_FFT = 2048                        # FFT window size
MIN_PITCH_HZ = 60.0                 # below this is likely noise (Hz)
MAX_PITCH_HZ = 400.0                # above this is likely noise/artifact (Hz)
SILENCE_THRESHOLD_DB = -40.0        # dBFS — below this is considered silence/pause
MIN_PAUSE_DURATION_S = 0.3          # seconds — shorter gaps don't count as pauses


@dataclass
class PitchRange:
    min_hz: float
    max_hz: float
    mean_hz: float
    std_hz: float
    voiced_fraction: float          # fraction of frames with detected pitch (0.0-1.0)


@dataclass
class SpeechRhythm:
    tempo_bpm: float                # overall speech tempo estimate
    articulation_rate: float        # syllables per second (approximated via onset density)
    speaking_rate_wpm: Optional[float] = None   # words per minute (if transcript available)


@dataclass
class EmotionalCadence:
    energy_variance: float          # variance of RMS energy envelope
    spectral_centroid_mean: float   # mean spectral centroid Hz (brightness)
    spectral_centroid_std: float    # std dev of spectral centroid (brightness variation)
    spectral_rolloff_mean: float    # mean spectral rolloff Hz


@dataclass
class PausePatterns:
    mean_pause_duration_s: float    # average silence duration in seconds
    pause_frequency_per_min: float  # pauses per minute
    total_pause_time_s: float       # total time in silence
    speaking_ratio: float           # fraction of time actually speaking (0.0-1.0)


@dataclass
class VolumeVariation:
    rms_mean: float                 # mean RMS energy (linear)
    rms_std: float                  # std dev of RMS energy (volume variation indicator)
    rms_mean_db: float              # mean RMS in dBFS
    dynamic_range_db: float         # difference between loudest and quietest 10th percentiles


@dataclass
class AcousticFeatures:
    """
    Complete acoustic feature set for one voice recording.

    This is the canonical output of the Omi acoustic analysis pipeline.
    These fields are stored in recordings.acoustic_metadata (JSON)
    and passed to the Celery+Claude personality analysis job.
    """
    # Core feature groups
    pitch_range: PitchRange
    speech_rhythm: SpeechRhythm
    emotional_cadence: EmotionalCadence
    pause_patterns: PausePatterns
    volume_variation: VolumeVariation

    # Recording metadata
    duration_seconds: float
    sample_rate: int
    analysis_version: str = "1.0"

    def to_dict(self) -> dict:
        """
        Serialize to the dict format stored in recordings.acoustic_metadata.
        All nested dataclasses are flattened by group name.
        """
        return {
            "pitch_range": asdict(self.pitch_range),
            "speech_rhythm": asdict(self.speech_rhythm),
            "emotional_cadence": asdict(self.emotional_cadence),
            "pause_patterns": asdict(self.pause_patterns),
            "volume_variation": asdict(self.volume_variation),
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "analysis_version": self.analysis_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AcousticFeatures":
        """Deserialize from acoustic_metadata JSON dict."""
        return cls(
            pitch_range=PitchRange(**data["pitch_range"]),
            speech_rhythm=SpeechRhythm(**data["speech_rhythm"]),
            emotional_cadence=EmotionalCadence(**data["emotional_cadence"]),
            pause_patterns=PausePatterns(**data["pause_patterns"]),
            volume_variation=VolumeVariation(**data["volume_variation"]),
            duration_seconds=data["duration_seconds"],
            sample_rate=data["sample_rate"],
            analysis_version=data.get("analysis_version", "1.0"),
        )


class AcousticExtractor:
    """
    Extracts acoustic personality features from a voice recording using librosa.

    Usage:
        extractor = AcousticExtractor()
        features = extractor.extract(audio_path="/path/to/recording.wav")
        acoustic_dict = features.to_dict()
        # Pass acoustic_dict as part of Celery job payload for Claude analysis

    The extractor accepts:
    - File path (str or Path)
    - Raw audio bytes + content_type
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.target_sr = sample_rate
        self._librosa_available = self._check_librosa()

    def _check_librosa(self) -> bool:
        try:
            import librosa  # noqa: F401
            import numpy  # noqa: F401
            return True
        except ImportError:
            logger.error(
                "librosa or numpy not installed. "
                "Install: pip install librosa numpy soundfile"
            )
            return False

    def extract(
        self,
        audio_input: Union[str, Path, bytes],
        content_type: str = "audio/wav",
        transcript: Optional[str] = None,
    ) -> AcousticFeatures:
        """
        Extract acoustic features from audio.

        Args:
            audio_input: File path (str/Path) or raw audio bytes
            content_type: MIME type (only needed if audio_input is bytes)
            transcript: Optional transcript text (used to compute speaking_rate_wpm)

        Returns:
            AcousticFeatures dataclass with all extracted features

        Raises:
            AcousticExtractionError if librosa is unavailable or audio is invalid
        """
        if not self._librosa_available:
            raise AcousticExtractionError(
                "librosa not available — cannot extract acoustic features"
            )

        import librosa
        import numpy as np

        # Load audio
        if isinstance(audio_input, bytes):
            y, sr = self._load_from_bytes(audio_input, content_type)
        else:
            audio_path = Path(audio_input)
            if not audio_path.exists():
                raise AcousticExtractionError(f"Audio file not found: {audio_path}")
            try:
                y, sr = librosa.load(str(audio_path), sr=self.target_sr, mono=True)
            except Exception as exc:
                raise AcousticExtractionError(
                    f"librosa failed to load {audio_path}: {exc}"
                ) from exc

        if len(y) == 0:
            raise AcousticExtractionError("Audio is empty or unreadable")

        duration_seconds = float(len(y) / sr)
        logger.info(
            f"Extracting acoustic features: {duration_seconds:.1f}s audio, sr={sr}"
        )

        # Extract each feature group
        pitch = self._extract_pitch(y, sr)
        rhythm = self._extract_rhythm(y, sr, transcript=transcript, duration=duration_seconds)
        cadence = self._extract_emotional_cadence(y, sr)
        pauses = self._extract_pause_patterns(y, sr)
        volume = self._extract_volume_variation(y, sr)

        return AcousticFeatures(
            pitch_range=pitch,
            speech_rhythm=rhythm,
            emotional_cadence=cadence,
            pause_patterns=pauses,
            volume_variation=volume,
            duration_seconds=duration_seconds,
            sample_rate=sr,
        )

    def extract_to_dict(
        self,
        audio_input: Union[str, Path, bytes],
        content_type: str = "audio/wav",
        transcript: Optional[str] = None,
    ) -> dict:
        """
        Convenience method: extract features and return as dict.
        This is what gets stored in recordings.acoustic_metadata.
        """
        features = self.extract(audio_input, content_type=content_type, transcript=transcript)
        return features.to_dict()

    # ── Feature extraction methods ────────────────────────────────────────

    def _extract_pitch(self, y, sr) -> PitchRange:
        """
        Extract pitch range using librosa PYIN algorithm.
        PYIN is more accurate than YIN for speech, handles unvoiced frames well.
        """
        import librosa
        import numpy as np

        try:
            # pyin returns (f0, voiced_flag, voiced_prob)
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=MIN_PITCH_HZ,
                fmax=MAX_PITCH_HZ,
                sr=sr,
                hop_length=HOP_LENGTH,
            )
        except Exception as exc:
            logger.warning(f"PYIN pitch extraction failed, falling back to piptrack: {exc}")
            return self._extract_pitch_fallback(y, sr)

        # Filter to voiced frames only
        voiced_f0 = f0[voiced_flag & ~np.isnan(f0)]

        voiced_fraction = float(np.sum(voiced_flag) / len(voiced_flag)) if len(voiced_flag) > 0 else 0.0

        if len(voiced_f0) == 0:
            logger.warning("No voiced frames detected in audio")
            return PitchRange(
                min_hz=0.0, max_hz=0.0, mean_hz=0.0, std_hz=0.0,
                voiced_fraction=voiced_fraction
            )

        # Use 5th/95th percentiles to exclude outliers
        min_hz = float(np.percentile(voiced_f0, 5))
        max_hz = float(np.percentile(voiced_f0, 95))
        mean_hz = float(np.mean(voiced_f0))
        std_hz = float(np.std(voiced_f0))

        return PitchRange(
            min_hz=round(min_hz, 2),
            max_hz=round(max_hz, 2),
            mean_hz=round(mean_hz, 2),
            std_hz=round(std_hz, 2),
            voiced_fraction=round(voiced_fraction, 3),
        )

    def _extract_pitch_fallback(self, y, sr) -> PitchRange:
        """Fallback pitch extraction using piptrack."""
        import librosa
        import numpy as np

        pitches, magnitudes = librosa.piptrack(y=y, sr=sr, fmin=MIN_PITCH_HZ, fmax=MAX_PITCH_HZ)
        pitch_values = []
        for t in range(pitches.shape[1]):
            idx = magnitudes[:, t].argmax()
            pitch = pitches[idx, t]
            if MIN_PITCH_HZ < pitch < MAX_PITCH_HZ:
                pitch_values.append(pitch)

        if not pitch_values:
            return PitchRange(min_hz=0.0, max_hz=0.0, mean_hz=0.0, std_hz=0.0, voiced_fraction=0.0)

        pitch_arr = np.array(pitch_values)
        return PitchRange(
            min_hz=round(float(np.percentile(pitch_arr, 5)), 2),
            max_hz=round(float(np.percentile(pitch_arr, 95)), 2),
            mean_hz=round(float(np.mean(pitch_arr)), 2),
            std_hz=round(float(np.std(pitch_arr)), 2),
            voiced_fraction=round(len(pitch_values) / max(pitches.shape[1], 1), 3),
        )

    def _extract_rhythm(
        self,
        y,
        sr,
        transcript: Optional[str] = None,
        duration: Optional[float] = None,
    ) -> SpeechRhythm:
        """
        Extract speech rhythm: tempo BPM and articulation rate.

        Tempo: estimated from onset envelope (how fast syllables/words arrive).
        Articulation rate: onset density in onsets/second (proxy for syllables/second).
        """
        import librosa
        import numpy as np

        # Onset detection for syllable rate estimation
        onset_frames = librosa.onset.onset_detect(
            y=y, sr=sr, hop_length=HOP_LENGTH, units="frames"
        )
        onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP_LENGTH)

        # Speech tempo from onset strength envelope
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
        try:
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            tempo_bpm = float(tempo) if not hasattr(tempo, '__len__') else float(tempo[0])
        except Exception:
            # Fallback: estimate from onset density
            actual_duration = duration or float(len(y) / sr)
            tempo_bpm = (len(onset_times) / actual_duration) * 60 if actual_duration > 0 else 0.0

        # Articulation rate: onsets per second (syllables/second approximation)
        actual_duration = duration or float(len(y) / sr)
        articulation_rate = len(onset_times) / actual_duration if actual_duration > 0 else 0.0

        # Words per minute (if transcript available)
        speaking_rate_wpm = None
        if transcript and actual_duration > 0:
            word_count = len(transcript.split())
            speaking_rate_wpm = round((word_count / actual_duration) * 60, 1)

        return SpeechRhythm(
            tempo_bpm=round(tempo_bpm, 1),
            articulation_rate=round(articulation_rate, 2),
            speaking_rate_wpm=speaking_rate_wpm,
        )

    def _extract_emotional_cadence(self, y, sr) -> EmotionalCadence:
        """
        Extract emotional cadence from energy envelope and spectral features.

        Energy variance: captures how much the speaker varies their energy (enthusiasm).
        Spectral centroid: represents "brightness" of the voice (higher = more energetic).
        """
        import librosa
        import numpy as np

        # RMS energy envelope
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        energy_variance = float(np.var(rms))

        # Spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(
            y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH
        )[0]
        centroid_mean = float(np.mean(spectral_centroid))
        centroid_std = float(np.std(spectral_centroid))

        # Spectral rolloff (frequency below which 85% of energy lies)
        rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH
        )[0]
        rolloff_mean = float(np.mean(rolloff))

        return EmotionalCadence(
            energy_variance=round(energy_variance, 6),
            spectral_centroid_mean=round(centroid_mean, 2),
            spectral_centroid_std=round(centroid_std, 2),
            spectral_rolloff_mean=round(rolloff_mean, 2),
        )

    def _extract_pause_patterns(self, y, sr) -> PausePatterns:
        """
        Extract pause patterns by detecting silence regions.

        Uses a dB threshold to identify silent (non-speech) frames.
        Merges adjacent silent frames into pause events.
        """
        import librosa
        import numpy as np

        # Compute RMS energy in dB
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        # Convert to dBFS (avoid log(0) with ref=np.max(rms) or small epsilon)
        max_rms = np.max(rms) if np.max(rms) > 0 else 1e-10
        rms_db = librosa.amplitude_to_db(rms, ref=max_rms)

        # Find silent frames
        silent_mask = rms_db < SILENCE_THRESHOLD_DB
        frame_duration = HOP_LENGTH / sr

        # Identify pause segments (consecutive silent frames)
        pauses = []
        in_pause = False
        pause_start = 0

        for i, is_silent in enumerate(silent_mask):
            if is_silent and not in_pause:
                in_pause = True
                pause_start = i
            elif not is_silent and in_pause:
                in_pause = False
                pause_duration = (i - pause_start) * frame_duration
                if pause_duration >= MIN_PAUSE_DURATION_S:
                    pauses.append(pause_duration)

        # Handle trailing pause
        if in_pause:
            pause_duration = (len(silent_mask) - pause_start) * frame_duration
            if pause_duration >= MIN_PAUSE_DURATION_S:
                pauses.append(pause_duration)

        total_duration = float(len(y) / sr)
        total_pause_time = sum(pauses)
        speaking_ratio = 1.0 - (total_pause_time / total_duration) if total_duration > 0 else 1.0

        pause_freq_per_min = (len(pauses) / total_duration * 60) if total_duration > 0 else 0.0
        mean_pause_duration = float(np.mean(pauses)) if pauses else 0.0

        return PausePatterns(
            mean_pause_duration_s=round(mean_pause_duration, 3),
            pause_frequency_per_min=round(pause_freq_per_min, 2),
            total_pause_time_s=round(total_pause_time, 2),
            speaking_ratio=round(max(0.0, min(1.0, speaking_ratio)), 3),
        )

    def _extract_volume_variation(self, y, sr) -> VolumeVariation:
        """
        Extract volume/energy variation metrics.

        RMS std dev: high value = expressive, dynamic speaker.
        Dynamic range: difference between loud and quiet moments.
        """
        import librosa
        import numpy as np

        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]

        # Filter out near-zero values (silence) for meaningful stats
        nonzero_rms = rms[rms > 1e-8]
        if len(nonzero_rms) == 0:
            nonzero_rms = rms

        rms_mean = float(np.mean(nonzero_rms))
        rms_std = float(np.std(nonzero_rms))

        # Convert mean to dBFS
        rms_mean_db = float(20 * np.log10(rms_mean + 1e-10))

        # Dynamic range: 90th percentile vs 10th percentile in dB
        p10 = float(np.percentile(nonzero_rms, 10))
        p90 = float(np.percentile(nonzero_rms, 90))
        dynamic_range_db = float(20 * np.log10((p90 + 1e-10) / (p10 + 1e-10)))

        return VolumeVariation(
            rms_mean=round(rms_mean, 6),
            rms_std=round(rms_std, 6),
            rms_mean_db=round(rms_mean_db, 2),
            dynamic_range_db=round(dynamic_range_db, 2),
        )

    def _load_from_bytes(self, audio_bytes: bytes, content_type: str):
        """Load audio from bytes using librosa + soundfile."""
        import librosa
        import io

        audio_buffer = io.BytesIO(audio_bytes)
        try:
            y, sr = librosa.load(audio_buffer, sr=self.target_sr, mono=True)
            return y, sr
        except Exception:
            # Fallback: write to temp file and reload
            import tempfile
            ext = _content_type_to_ext(content_type)
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            try:
                y, sr = librosa.load(tmp_path, sr=self.target_sr, mono=True)
                return y, sr
            finally:
                os.unlink(tmp_path)


def _content_type_to_ext(content_type: str) -> str:
    mapping = {
        "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
        "audio/wav": ".wav", "audio/x-wav": ".wav",
        "audio/m4a": ".m4a", "audio/x-m4a": ".m4a", "audio/mp4": ".m4a",
        "audio/ogg": ".ogg", "audio/flac": ".flac",
    }
    return mapping.get(content_type.split(";")[0].strip().lower(), ".wav")


class AcousticExtractionError(Exception):
    """Raised when acoustic feature extraction fails."""
    pass
