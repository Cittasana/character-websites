"""
Security validation utilities.
Run at startup to verify secret hygiene and connectivity.
S3/bucket encryption checks removed — Supabase Storage handles encryption.
"""
import logging
import os
import re
from typing import Any

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Secrets that should NEVER be default/empty ────────────────────────────────
_REQUIRED_SECRETS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "ANTHROPIC_API_KEY",
]

_INSECURE_SECRET_PATTERNS = [
    r"^REPLACE_WITH",
    r"^your[_-]",
    r"^secret$",
    r"^password$",
    r"^changeme$",
    r"^test$",
    r"^example",
]


def audit_environment_secrets() -> dict[str, Any]:
    """
    Verify all required secrets are set and non-default.
    Returns a dict with any issues found.
    """
    issues = []

    for secret_name in _REQUIRED_SECRETS:
        value = os.environ.get(secret_name, "")
        if not value:
            issues.append(f"SECRET MISSING: {secret_name} is not set")
            continue
        for pattern in _INSECURE_SECRET_PATTERNS:
            if re.match(pattern, value, re.IGNORECASE):
                issues.append(f"SECRET INSECURE: {secret_name} appears to use a placeholder value")
                break

    result = {"passed": len(issues) == 0, "issues": issues}
    if issues:
        for issue in issues:
            logger.warning("Security audit: %s", issue)
    else:
        logger.info("Security audit: all secrets OK")

    return result


def check_tls_enforcement() -> dict[str, Any]:
    """
    Verify TLS is enforced:
    - APP_ENV is not development with DEBUG=True in production
    - ALLOWED_ORIGINS uses HTTPS in production
    """
    issues = []

    if settings.APP_ENV == "production" and settings.DEBUG:
        issues.append("DEBUG=True is set in production environment — disable immediately")

    for origin in settings.ALLOWED_ORIGINS:
        if settings.APP_ENV == "production" and origin.startswith("http://"):
            issues.append(f"ALLOWED_ORIGINS contains non-HTTPS origin in production: {origin}")

    # Supabase URL must be HTTPS
    if not settings.SUPABASE_URL.startswith("https://"):
        issues.append("SUPABASE_URL must use HTTPS")

    return {"passed": len(issues) == 0, "issues": issues}


async def check_supabase_connectivity() -> dict[str, Any]:
    """
    Verify Supabase is reachable.
    """
    try:
        from app.supabase_client import check_supabase_health
        reachable = check_supabase_health()
        if not reachable:
            return {
                "passed": False,
                "issues": ["Supabase is not reachable — check SUPABASE_URL and credentials"],
            }
        logger.info("Supabase connectivity check: OK")
        return {"passed": True, "issues": []}
    except Exception as exc:
        return {
            "passed": False,
            "issues": [f"Could not verify Supabase connectivity: {exc}"],
        }


async def run_all_security_checks() -> dict[str, Any]:
    """
    Run all security checks and return combined results.
    Should be called at application startup in production.
    """
    results = {
        "secrets": audit_environment_secrets(),
        "tls": check_tls_enforcement(),
        "supabase": await check_supabase_connectivity(),
    }

    all_passed = all(r["passed"] for r in results.values())
    all_issues = []
    for check_name, result in results.items():
        for issue in result.get("issues", []):
            all_issues.append(f"[{check_name}] {issue}")

    return {
        "all_passed": all_passed,
        "checks": results,
        "issues": all_issues,
    }
