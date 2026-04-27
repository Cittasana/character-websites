"""
Rate-Limiting & Debouncing für Claude-API-Calls aus dem Omi-Sync-Pfad.

Drei Schutzschichten, alle in Redis (überleben Worker-Restarts):

1. **Per-User-Debounce** — Mehrere Omi-Recordings eines Users innerhalb eines
   Zeitfensters (CLAUDE_DEBOUNCE_SECONDS) werden zu **einer** Claude-Analyse
   koalesziert. Das ist die wichtigste Kosten-Bremse bei Omi-Bursts.

2. **Per-User-Tagesquota** — Hartes Cap (CLAUDE_MAX_PER_USER_PER_DAY) gegen
   Runaway-Kosten durch einen einzelnen User. Atomar via INCR+EXPIRE.

3. **Globaler Token-Bucket (RPM)** — Lua-Skript begrenzt die Claude-Requests
   über alle Celery-Worker hinweg auf CLAUDE_GLOBAL_RPM, damit wir nicht in
   Anthropic-API-Limits laufen.

Alle Redis-Operationen sind synchron (Celery-Tasks sind sync) und benutzen
einen process-lokalen Connection-Pool.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Redis-Client (sync, lazy) ─────────────────────────────────────────────────

_sync_redis: Optional[redis.Redis] = None


def get_sync_redis() -> redis.Redis:
    """Process-lokaler synchroner Redis-Client für Celery-Worker."""
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = redis.Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
    return _sync_redis


def reset_sync_redis() -> None:
    """Nur für Tests: erzwingt Neuverbindung."""
    global _sync_redis
    if _sync_redis is not None:
        try:
            _sync_redis.close()
        except Exception:
            pass
    _sync_redis = None


# ── Layer 1: Per-User-Debounce ────────────────────────────────────────────────

# Speichert die zuletzt gemeldete recording_id für einen User.
# Wird durch den scheduled Task atomar via GETDEL eingelöst.
_PENDING_KEY = "cw:claude:pending:{user_id}"
# Marker, dass für einen User bereits ein debounced Celery-Task läuft.
# SET NX EX → genau ein Scheduler pro Debounce-Fenster.
_SCHEDULED_KEY = "cw:claude:scheduled:{user_id}"

# TTL für den pending-Eintrag — großzügig, falls Worker länger braucht.
_PENDING_TTL_SECONDS = 86_400


def mark_user_pending(user_id: str, recording_id: str) -> None:
    """
    Hinterlege das **neueste** Recording als pending für diesen User.

    Überschreibt einen vorhandenen Eintrag (das ist gewollt — wir wollen
    immer das jüngste Transkript analysieren, ältere Bursts werden verworfen).
    """
    client = get_sync_redis()
    client.setex(_PENDING_KEY.format(user_id=user_id), _PENDING_TTL_SECONDS, recording_id)


def take_user_pending(user_id: str) -> Optional[str]:
    """
    Atomar: hole und lösche das pending-Recording für diesen User.

    Race-frei gegen gleichzeitig eintreffende neue Uploads — die werden
    NACH diesem Aufruf einen neuen pending-Eintrag setzen und einen neuen
    Debounce-Cycle starten.
    """
    client = get_sync_redis()
    return client.execute_command("GETDEL", _PENDING_KEY.format(user_id=user_id))


def try_schedule_user_analysis(user_id: str, debounce_seconds: int) -> bool:
    """
    Versuche, einen neuen Debounce-Cycle für diesen User zu starten.

    Returns:
        True  → Caller soll jetzt einen Celery-Task mit
                ``countdown=debounce_seconds`` schedulen.
        False → Es läuft bereits ein scheduled Task innerhalb des Fensters
                (nichts tun, das pending-Recording wird beim Feuern
                eingelesen).

    Atomar via SET NX EX.
    """
    client = get_sync_redis()
    key = _SCHEDULED_KEY.format(user_id=user_id)
    return bool(client.set(key, "1", nx=True, ex=debounce_seconds))


def clear_scheduled_marker(user_id: str) -> None:
    """Nach dem Feuern eines scheduled Tasks: erlaube neuen Cycle."""
    client = get_sync_redis()
    client.delete(_SCHEDULED_KEY.format(user_id=user_id))


# ── Layer 2: Per-User-Tagesquota ──────────────────────────────────────────────

_QUOTA_KEY = "cw:claude:quota:{user_id}:{day}"


def _utc_day_str() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def consume_user_quota(user_id: str, max_per_day: int) -> bool:
    """
    Atomar: erhöhe den Tageszähler des Users.

    Returns:
        True  → Quota ok, Claude-Call darf laufen.
        False → Quota überschritten — Caller muss skipnen oder verschieben.

    Wenn überschritten, wird der Counter wieder dekrementiert (kein
    permanentes Hochschrauben durch abgelehnte Versuche).
    """
    client = get_sync_redis()
    key = _QUOTA_KEY.format(user_id=user_id, day=_utc_day_str())
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 86_400 * 2)  # zwei Tage TTL → robust gegen UTC-Übergang
    new_count, _ = pipe.execute()
    if new_count > max_per_day:
        client.decr(key)
        return False
    return True


def get_user_quota_used(user_id: str) -> int:
    """Anzahl der heute bereits konsumierten Claude-Calls dieses Users."""
    client = get_sync_redis()
    raw = client.get(_QUOTA_KEY.format(user_id=user_id, day=_utc_day_str()))
    return int(raw) if raw else 0


def refund_user_quota(user_id: str) -> int:
    """
    Best-effort Decrement nach abgebrochenem Claude-Call.

    Wird genutzt, wenn ``consume_user_quota`` schon erfolgte, aber der
    eigentliche Call nicht stattfindet (z. B. globaler Token-Bucket lief in
    Timeout). Verhindert, dass eine retry-Welle die Quota fälschlich aufzehrt.
    """
    client = get_sync_redis()
    return int(client.decr(_QUOTA_KEY.format(user_id=user_id, day=_utc_day_str())))


def seconds_until_utc_midnight() -> int:
    """Sekunden bis zum nächsten UTC-Quota-Reset (00:00 UTC + 60s Puffer)."""
    now = datetime.now(tz=timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight = midnight.replace(day=now.day) + _one_day()
    return int((midnight - now).total_seconds()) + 60


def _one_day():
    from datetime import timedelta
    return timedelta(days=1)


# ── Layer 3: Globaler Token-Bucket (Anthropic-RPM) ────────────────────────────

_GLOBAL_BUCKET_KEY = "cw:claude:globalbucket"

# Atomares Token-Bucket-Skript:
#   KEYS[1] = Bucket-Key (gespeichert: "<tokens>|<last_refill_ms>")
#   ARGV[1] = capacity        (max Tokens)
#   ARGV[2] = refill_per_sec  (Tokens pro Sekunde)
#   ARGV[3] = now_ms          (aktuelle Zeit ms)
# Returns: {1|0 consumed, math.floor(remaining)}
_TOKEN_BUCKET_LUA = """
local data = redis.call("GET", KEYS[1])
local capacity = tonumber(ARGV[1])
local refill_per_sec = tonumber(ARGV[2])
local now_ms = tonumber(ARGV[3])
local tokens
local last
if data then
  local sep = string.find(data, "|")
  tokens = tonumber(string.sub(data, 1, sep - 1))
  last = tonumber(string.sub(data, sep + 1))
else
  tokens = capacity
  last = now_ms
end
local delta_sec = (now_ms - last) / 1000.0
if delta_sec < 0 then delta_sec = 0 end
local new_tokens = math.min(capacity, tokens + delta_sec * refill_per_sec)
local consumed = 0
if new_tokens >= 1 then
  new_tokens = new_tokens - 1
  consumed = 1
end
redis.call("SET", KEYS[1], string.format("%.4f", new_tokens) .. "|" .. now_ms, "EX", 600)
return {consumed, math.floor(new_tokens)}
"""


def acquire_global_token(timeout_seconds: float | None = None) -> bool:
    """
    Blockiere, bis ein globaler RPM-Token verfügbar ist.

    Diese Drossel gilt prozessübergreifend für ALLE Celery-Worker.

    Returns:
        True  → Token bekommen, Claude-Call darf raus.
        False → Innerhalb von ``timeout_seconds`` kein Token verfügbar.

    Beim Bucket-Limit ist Sleep ≈ 1 / refill_per_sec, mindestens 50 ms.
    """
    if timeout_seconds is None:
        timeout_seconds = settings.CLAUDE_GLOBAL_TOKEN_TIMEOUT_SECONDS

    capacity = max(1, settings.CLAUDE_GLOBAL_RPM)
    refill_per_sec = capacity / 60.0
    sleep_step = max(0.05, min(1.0, 1.0 / refill_per_sec))
    deadline = time.monotonic() + timeout_seconds

    client = get_sync_redis()
    while True:
        consumed, _remaining = client.eval(
            _TOKEN_BUCKET_LUA,
            1,
            _GLOBAL_BUCKET_KEY,
            capacity,
            refill_per_sec,
            int(time.time() * 1000),
        )
        if consumed:
            return True
        if time.monotonic() >= deadline:
            logger.warning(
                "claude global token bucket: timeout after %.1fs (RPM=%d)",
                timeout_seconds, capacity,
            )
            return False
        time.sleep(sleep_step)
