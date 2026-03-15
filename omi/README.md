# Omi Integration Layer

Character-Websites wearable voice integration — Phases 11-13.

## Overview

The Omi layer connects users' [Omi AI wearable devices](https://github.com/BasedHardware/omi) to the Character-Websites platform. It automatically syncs voice recordings, generates transcripts, extracts acoustic personality features, and feeds them into the Claude analysis pipeline.

## Architecture

```
Omi Device (BLE)
      │
      ▼
Omi Cloud API (https://api.omi.me)
      │ OAuth 2.0
      ▼
┌─────────────────────────────────────────┐
│         Omi Integration Layer           │
│                                         │
│  Phase 11: Device Pairing               │
│  ├── bluetooth.py  (BLE discovery)      │
│  ├── oauth.py      (OAuth 2.0 flow)     │
│  └── device_manager.py (device ↔ user) │
│                                         │
│  Phase 12: Audio Sync Pipeline          │
│  ├── detector.py   (poll Omi API)       │
│  ├── downloader.py (→ encrypted buffer) │
│  ├── deduplicator.py (SHA-256 check)   │
│  ├── uploader.py   (→ backend API)      │
│  └── queue.py      (offline retry)     │
│                                         │
│  Transcription:                         │
│  └── whisper_fallback.py               │
│                                         │
│  Phase 13: Acoustic Analysis + Privacy  │
│  ├── extractor.py  (librosa features)  │
│  └── controls.py   (delete/reset/sync) │
│                                         │
│  sync_orchestrator.py (main loop)       │
└─────────────────────────────────────────┘
      │
      ▼
Backend API (POST /api/upload/voice)
      │
      ▼
Celery Worker → Claude Analysis
```

## Setup

### 1. Install dependencies

```bash
cd /path/to/CW
pip install -r omi/requirements.txt
```

### 2. Environment Variables

Copy and fill in `.env` at the project root:

```env
# Omi OAuth App (register at https://github.com/BasedHardware/omi/tree/main/backend)
OMI_APP_ID=your-app-id
OMI_CLIENT_ID=your-client-id
OMI_CLIENT_SECRET=your-client-secret
OMI_OAUTH_REDIRECT_URI=https://yourapp.com/api/omi/callback

# Backend API
BACKEND_API_URL=http://localhost:8000
BACKEND_JWT_SECRET=your-service-jwt

# Encryption key for temp audio buffers
# Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TEMP_BUFFER_ENCRYPTION_KEY=your-fernet-key

# Whisper transcription (one of:)
OPENAI_API_KEY=your-openai-key      # For Whisper API
# WHISPER_USE_LOCAL=true            # For local whisper model
# WHISPER_LOCAL_MODEL=base          # base|small|medium|large

# Sync settings
SYNC_POLL_INTERVAL_SECONDS=300      # 5 minutes
OFFLINE_QUEUE_PATH=/tmp/omi_offline_queue
```

### 3. Register your Omi App

1. Self-host the Omi backend or use the official Omi platform
2. Register a new "App" with capability `conversations:read`
3. Set webhook URL (optional) or use polling (default)
4. Get your `app_id`, `client_id`, `client_secret`

## Usage

### Pairing a Device

```python
import asyncio
from omi.pairing.oauth import OmiOAuthClient
from omi.pairing.device_manager import DeviceManager

async def pair_device(user_id: str, user_jwt: str):
    client = OmiOAuthClient()

    # Step 1: Get authorization URL (redirect user here)
    auth_url, state = client.get_authorization_url()
    print(f"Redirect user to: {auth_url}")

    # Step 2: After redirect callback with code:
    # tokens = await client.exchange_code(code=request.code)

    # Step 3: Store pairing
    # manager = DeviceManager(backend_jwt=user_jwt)
    # await manager.pair_device(user_id=user_id, tokens=tokens)
```

### Running a Sync Cycle

```python
import asyncio
from omi.sync_orchestrator import run_sync_for_user

async def sync():
    result = await run_sync_for_user(
        user_id="user-uuid",
        user_jwt="user-bearer-token",
    )
    print(f"Uploaded: {result.recordings_uploaded}")
    print(f"Errors: {result.errors}")

asyncio.run(sync())
```

### Acoustic Feature Extraction

```python
from omi.acoustic.extractor import AcousticExtractor

extractor = AcousticExtractor()

# From file path
features = extractor.extract("/path/to/recording.wav")
acoustic_dict = features.to_dict()
# acoustic_dict is stored in recordings.acoustic_metadata

# From bytes
features = extractor.extract(audio_bytes, content_type="audio/wav")
```

### Privacy Controls

```python
import asyncio
from omi.privacy.controls import PrivacyControls, SyncSettings

async def privacy_ops(user_jwt: str):
    controls = PrivacyControls(user_jwt=user_jwt)

    # Delete a recording
    result = await controls.delete_recording("recording-uuid")

    # Delete all voice data + reset personality
    result = await controls.delete_all_voice_data(also_reset_personality=True)

    # Disable sync
    await controls.update_sync_settings(SyncSettings(sync_enabled=False))

    # Get sync status (for dashboard)
    status = await controls.get_sync_status()
    print(status.to_dict())
```

## Acoustic Features

The extractor outputs a JSON dict matching `recordings.acoustic_metadata`:

```json
{
  "pitch_range": {
    "min_hz": 98.5,
    "max_hz": 245.0,
    "mean_hz": 165.3,
    "std_hz": 28.4,
    "voiced_fraction": 0.72
  },
  "speech_rhythm": {
    "tempo_bpm": 142.5,
    "articulation_rate": 3.8,
    "speaking_rate_wpm": 165.0
  },
  "emotional_cadence": {
    "energy_variance": 0.000234,
    "spectral_centroid_mean": 2150.4,
    "spectral_centroid_std": 380.2,
    "spectral_rolloff_mean": 4200.0
  },
  "pause_patterns": {
    "mean_pause_duration_s": 0.42,
    "pause_frequency_per_min": 18.5,
    "total_pause_time_s": 12.3,
    "speaking_ratio": 0.68
  },
  "volume_variation": {
    "rms_mean": 0.0234,
    "rms_std": 0.0089,
    "rms_mean_db": -32.6,
    "dynamic_range_db": 14.2
  },
  "duration_seconds": 47.3,
  "sample_rate": 22050,
  "analysis_version": "1.0"
}
```

These fields are passed alongside the transcript in the Celery job payload when Claude performs personality analysis.

## Running Tests

```bash
cd /path/to/CW
pip install -r omi/requirements.txt
pytest omi/tests/ -v
```

## Backend API Contracts

The Omi layer expects these backend endpoints (implemented by the Backend team):

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/voice` | Upload voice recording |
| GET | `/api/upload/voice/check-duplicate` | Deduplication check |
| PATCH | `/api/upload/voice/:id/acoustic` | Attach acoustic metadata |
| DELETE | `/api/upload/voice/:id` | Delete individual recording |
| DELETE | `/api/upload/voice/all` | Delete all voice data |
| PATCH | `/api/upload/voice/settings` | Update sync settings |
| GET | `/api/upload/voice/settings` | Get sync settings |
| POST | `/api/omi/devices` | Store device pairing |
| GET | `/api/omi/devices/:userId` | Get pairing data |
| PATCH | `/api/omi/devices/:userId` | Update pairing data |
| DELETE | `/api/omi/devices/:userId` | Remove pairing |
| GET | `/api/omi/sync/status` | Get sync status |
| PATCH | `/api/omi/sync/status` | Update last_sync_at |
