# API Contracts: Omi ↔ Backend

_Generated: 2026-03-15_

## Summary

The Omi sync layer communicates with the backend via HTTP (httpx). This document validates
each call made by `omi/pairing/device_manager.py` and `omi/sync_orchestrator.py` against
the backend routes defined in `backend/app/routes/omi/devices.py` and
`backend/app/routes/upload/voice.py`.

---

## 1. Device Pairing Endpoints

### POST /api/omi/devices — Pair a device

**Omi caller:** `DeviceManager.pair_device()` (`omi/pairing/device_manager.py:140`)

**Payload sent by Omi:**
```json
{
  "user_id": "uuid",
  "device_id": "string",
  "omi_uid": "string | null",
  "omi_access_token": "string",
  "omi_refresh_token": "string | null",
  "token_expires_at": "ISO string | null",
  "paired_at": "ISO string",
  "last_seen": "ISO string | null",
  "battery_level": "int | null",
  "is_active": true
}
```

**Backend `DevicePairRequest` schema (`devices.py:25`):**
```python
class DevicePairRequest(BaseModel):
    device_id: str
    omi_access_token: str
```

**MISMATCH — SEVERITY: MEDIUM**

The Omi layer sends a full `DevicePairingData` dict (10 fields) but the backend only
accepts `device_id` + `omi_access_token`. Extra fields are silently ignored by Pydantic,
so the call does not error, but the following fields sent by Omi are **not persisted**:
- `omi_uid`
- `omi_refresh_token`
- `token_expires_at`
- `paired_at`
- `last_seen`
- `battery_level`
- `is_active`

This means token refresh (`ensure_token_fresh`) cannot work correctly because
`omi_refresh_token` and `token_expires_at` are never stored.

**Fix required:** Extend `DevicePairRequest` in `backend/app/routes/omi/devices.py` to
accept all fields from `DevicePairingData`, or the Omi layer should be updated to send
only what the backend accepts. Recommended: extend the backend to accept the full payload.

---

### GET /api/omi/devices/{user_id} — Get pairing data

**Omi caller:** `DeviceManager.get_pairing_data()` (`devices.py:276`)
Expects: a dict matching `DevicePairingData` fields (10 fields).

**Backend `DevicePairResponse` schema:**
```python
class DevicePairResponse(BaseModel):
    user_id: uuid.UUID
    device_id: str
    paired: bool
    paired_at: str | None
```

**MISMATCH — SEVERITY: HIGH**

The Omi layer does `DevicePairingData(**raw)` on the response JSON, but the backend
returns only `{user_id, device_id, paired, paired_at}`. Missing fields required by Omi:
- `omi_uid`
- `omi_access_token` (critical — used for Omi API calls)
- `omi_refresh_token`
- `token_expires_at`
- `last_seen`
- `battery_level`
- `is_active`

The `DevicePairingData(**raw)` call will raise a `TypeError` because `omi_access_token`
is a required field in the dataclass.

**Fix required:** The backend GET endpoint must return all pairing fields, including the
access/refresh tokens. This is a security-sensitive change (tokens in response body) —
ensure this endpoint is strictly auth-gated to the owner only (already is via
`str(current_user.id) != str(user_id)` check).

---

### PATCH /api/omi/devices/{user_id} — Update device / token refresh

**Omi callers (multiple):**
1. `ensure_token_fresh()` — sends `{omi_access_token, omi_refresh_token, token_expires_at}`
2. `update_last_seen()` — sends `{last_seen, battery_level?}`
3. `_deactivate_device()` — sends `{is_active: false}`

**Backend `DeviceUpdateRequest` schema:**
```python
class DeviceUpdateRequest(BaseModel):
    omi_access_token: str
```

**MISMATCH — SEVERITY: HIGH**

The backend PATCH only accepts `omi_access_token`. It cannot handle:
- `last_seen` / `battery_level` updates (used by `update_last_seen`)
- `is_active` flag (used by `_deactivate_device`)
- `omi_refresh_token` / `token_expires_at` (used by `ensure_token_fresh`)

The calls to PATCH with unrecognized fields will cause Pydantic validation errors (422).

**Fix required:** Make `DeviceUpdateRequest` fields all optional (or use a freeform dict
pattern) so each caller can send only the fields it needs. Example:

```python
class DeviceUpdateRequest(BaseModel):
    omi_access_token: str | None = None
    omi_refresh_token: str | None = None
    token_expires_at: str | None = None
    last_seen: str | None = None
    battery_level: int | None = None
    is_active: bool | None = None
```

---

### DELETE /api/omi/devices/{user_id} — Unpair

**Omi caller:** `DeviceManager.unpair_device()` — no body, path param only.
**Backend route:** accepts `user_id` UUID path param, no body, returns 204.

**STATUS: MATCH** — No issues.

---

## 2. Voice Upload Endpoints

### POST /api/upload/voice — Upload audio

**Omi caller:** `AudioUploader.upload_from_buffer()` / `upload_from_path()`
(referenced in `sync_orchestrator.py:273`; actual HTTP call in `omi/sync/uploader.py`)

**Backend route:** `POST /api/upload/voice` — multipart form data, field name `file`.
Returns `VoiceUploadResponse`:
```json
{
  "recording_id": "uuid",
  "storage_path": "string",
  "original_filename": "string",
  "file_size_bytes": "int",
  "detected_mime": "string",
  "processing_status": "string",
  "message": "string"
}
```

**STATUS: MATCH** — The response field `recording_id` is used by the Omi uploader
(`upload_result.recording_id`) which aligns with the backend response schema.

---

### PATCH /api/upload/voice/{recording_id}/acoustic — Attach acoustic metadata

**Omi caller:** `SyncOrchestrator._attach_acoustic_metadata()` (`sync_orchestrator.py:435`)

```python
await client.patch(
    f"/api/upload/voice/{recording_id}/acoustic",
    json={"acoustic_metadata": acoustic_metadata},
)
```

**Backend route:** `PATCH /api/upload/voice/{recording_id}/acoustic`
Accepts: `acoustic_metadata: dict` (raw dict in body, not wrapped in a key).

**MISMATCH — SEVERITY: LOW**

The Omi caller wraps the metadata in `{"acoustic_metadata": acoustic_metadata}` but the
backend route signature is `async def patch_acoustic_metadata(recording_id, acoustic_metadata: dict, ...)`.
FastAPI will try to parse the request body as the raw `dict` (not a nested key).

The backend should use a Pydantic model:
```python
class AcousticMetadataRequest(BaseModel):
    acoustic_metadata: dict

async def patch_acoustic_metadata(
    recording_id: uuid.UUID,
    body: AcousticMetadataRequest,
    ...
)
```

This will make the Omi payload `{"acoustic_metadata": {...}}` deserialize correctly.

---

### GET /api/upload/voice/check-duplicate — Deduplication check

**Omi caller:** `RecordingDeduplicator.is_duplicate()` (referenced in `sync_orchestrator.py:217`)

**Backend route:** `GET /api/upload/voice/check-duplicate?sha256=&omi_id=`
Returns: `{"is_duplicate": bool}`

**STATUS: MATCH** — Shape aligns.

---

## 3. Summary Table

| Endpoint | Status | Severity |
|----------|--------|----------|
| POST /api/omi/devices | MISMATCH — backend accepts too few fields | MEDIUM |
| GET /api/omi/devices/{user_id} | MISMATCH — response missing required Omi fields | HIGH |
| PATCH /api/omi/devices/{user_id} | MISMATCH — only accepts omi_access_token | HIGH |
| DELETE /api/omi/devices/{user_id} | MATCH | — |
| POST /api/upload/voice | MATCH | — |
| PATCH /api/upload/voice/{id}/acoustic | MISMATCH — body wrapping mismatch | LOW |
| GET /api/upload/voice/check-duplicate | MATCH | — |

---

## 4. Recommended Priority Fixes

1. **[HIGH]** Extend `GET /api/omi/devices/{user_id}` response to include all
   `DevicePairingData` fields including tokens. Auth-gate is already in place.

2. **[HIGH]** Extend `PATCH /api/omi/devices/{user_id}` to accept partial updates
   for all device fields (tokens, last_seen, battery_level, is_active).

3. **[MEDIUM]** Extend `POST /api/omi/devices` to persist full pairing data
   (omi_refresh_token, token_expires_at, omi_uid) — required for token refresh to work.

4. **[LOW]** Add Pydantic wrapper model for `PATCH /api/upload/voice/{id}/acoustic`
   so `{"acoustic_metadata": {...}}` deserializes correctly.
