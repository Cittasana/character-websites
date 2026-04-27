"""
Unit tests for app.jobs.rate_limiter.

Use MagicMock-based fakes for Redis so the suite does not need a live
Redis instance. The integration with Lua / real Redis is covered by the
existing load tests.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.jobs import rate_limiter as rl


@pytest.fixture(autouse=True)
def _reset_redis_singleton():
    rl.reset_sync_redis()
    yield
    rl.reset_sync_redis()


def _make_fake_redis() -> MagicMock:
    """Build a Redis-like mock with the methods rate_limiter touches."""
    client = MagicMock()
    pipeline = MagicMock()
    pipeline.incr.return_value = pipeline
    pipeline.expire.return_value = pipeline
    pipeline.execute.return_value = [1, True]
    client.pipeline.return_value = pipeline
    client.set.return_value = True
    client.execute_command.return_value = None
    client.get.return_value = None
    client.decr.return_value = 0
    client.delete.return_value = 1
    client.eval.return_value = [1, 5]
    return client


# ── Layer 1 — Per-user debounce ──────────────────────────────────────────────


class TestUserPending:
    def test_mark_user_pending_sets_with_ttl(self) -> None:
        fake = _make_fake_redis()
        with patch.object(rl, "get_sync_redis", return_value=fake):
            rl.mark_user_pending("user-1", "rec-abc")
        fake.setex.assert_called_once()
        args, _ = fake.setex.call_args
        assert args[0] == "cw:claude:pending:user-1"
        assert args[1] == rl._PENDING_TTL_SECONDS
        assert args[2] == "rec-abc"

    def test_take_user_pending_uses_getdel(self) -> None:
        fake = _make_fake_redis()
        fake.execute_command.return_value = "rec-xyz"
        with patch.object(rl, "get_sync_redis", return_value=fake):
            value = rl.take_user_pending("user-2")
        fake.execute_command.assert_called_once_with(
            "GETDEL", "cw:claude:pending:user-2",
        )
        assert value == "rec-xyz"

    def test_take_user_pending_returns_none_when_empty(self) -> None:
        fake = _make_fake_redis()
        fake.execute_command.return_value = None
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.take_user_pending("user-3") is None

    def test_try_schedule_user_analysis_true_on_first_call(self) -> None:
        fake = _make_fake_redis()
        fake.set.return_value = True
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.try_schedule_user_analysis("user-1", 600) is True
        fake.set.assert_called_once_with(
            "cw:claude:scheduled:user-1", "1", nx=True, ex=600,
        )

    def test_try_schedule_user_analysis_false_when_already_armed(self) -> None:
        fake = _make_fake_redis()
        fake.set.return_value = None  # SET NX returns None when key exists
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.try_schedule_user_analysis("user-1", 600) is False


# ── Layer 2 — Per-user daily quota ───────────────────────────────────────────


class TestUserQuota:
    def test_consume_within_limit(self) -> None:
        fake = _make_fake_redis()
        fake.pipeline.return_value.execute.return_value = [3, True]
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.consume_user_quota("user-1", max_per_day=30) is True

    def test_consume_above_limit_refunds(self) -> None:
        fake = _make_fake_redis()
        fake.pipeline.return_value.execute.return_value = [31, True]
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.consume_user_quota("user-1", max_per_day=30) is False
        # Counter must be rolled back so a stalled user does not stay
        # over-budget for the rest of the day.
        fake.decr.assert_called_once()

    def test_refund_user_quota_decrements(self) -> None:
        fake = _make_fake_redis()
        fake.decr.return_value = 5
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.refund_user_quota("user-1") == 5
        fake.decr.assert_called_once()

    def test_seconds_until_utc_midnight_is_positive(self) -> None:
        seconds = rl.seconds_until_utc_midnight()
        assert 60 < seconds <= 86_400 + 60


# ── Layer 3 — Global Anthropic-RPM token bucket ──────────────────────────────


class TestGlobalTokenBucket:
    def test_acquire_returns_true_when_token_available(self) -> None:
        fake = _make_fake_redis()
        fake.eval.return_value = [1, 5]
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.acquire_global_token(timeout_seconds=0.5) is True
        fake.eval.assert_called()

    def test_acquire_returns_false_after_timeout(self) -> None:
        fake = _make_fake_redis()
        fake.eval.return_value = [0, 0]  # bucket always empty
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.acquire_global_token(timeout_seconds=0.05) is False
        # Must have polled at least once.
        assert fake.eval.call_count >= 1

    def test_acquire_consumes_after_polling(self) -> None:
        """Returns True as soon as eval reports a consumed token."""
        fake = _make_fake_redis()
        # First call empty, second call consumed.
        fake.eval.side_effect = [[0, 0], [1, 4]]
        with patch.object(rl, "get_sync_redis", return_value=fake):
            assert rl.acquire_global_token(timeout_seconds=2.0) is True
        assert fake.eval.call_count == 2
