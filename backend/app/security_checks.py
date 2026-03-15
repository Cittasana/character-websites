"""
Phase 5 security validation utilities.
Run at startup to verify encryption, TLS, and secret hygiene.
"""
import logging
import os
import re
from typing import Any

from app.config import get_settings
from app.storage import verify_bucket_encryption

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Secrets that should NEVER be default/empty ────────────────────────────────
_REQUIRED_SECRETS = [
    "JWT_SECRET_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "S3_BUCKET_NAME",
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

    # JWT secret should be at least 32 chars
    jwt_key = os.environ.get("JWT_SECRET_KEY", "")
    if jwt_key and len(jwt_key) < 32:
        issues.append("JWT_SECRET_KEY is too short (minimum 32 characters recommended)")

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
    - DATABASE_URL uses SSL
    - APP_ENV is not development with DEBUG=True in production
    """
    issues = []

    db_url = os.environ.get("DATABASE_URL", "")
    if settings.APP_ENV == "production" and "sslmode=require" not in db_url:
        issues.append(
            "DATABASE_URL should include ?sslmode=require in production"
        )

    if settings.APP_ENV == "production" and settings.DEBUG:
        issues.append("DEBUG=True is set in production environment — disable immediately")

    # Check ALLOWED_ORIGINS doesn't include http:// in production
    for origin in settings.ALLOWED_ORIGINS:
        if settings.APP_ENV == "production" and origin.startswith("http://"):
            issues.append(f"ALLOWED_ORIGINS contains non-HTTPS origin in production: {origin}")

    return {"passed": len(issues) == 0, "issues": issues}


async def check_s3_encryption() -> dict[str, Any]:
    """
    Verify S3 bucket has server-side encryption enabled.
    """
    try:
        encrypted = verify_bucket_encryption()
        if not encrypted:
            return {
                "passed": False,
                "issues": [f"S3 bucket '{settings.S3_BUCKET_NAME}' does NOT have server-side encryption enabled"],
            }
        logger.info("S3 encryption check: bucket %s is encrypted", settings.S3_BUCKET_NAME)
        return {"passed": True, "issues": []}
    except Exception as exc:
        return {
            "passed": False,
            "issues": [f"Could not verify S3 encryption: {exc}"],
        }


async def run_all_security_checks() -> dict[str, Any]:
    """
    Run all security checks and return combined results.
    Should be called at application startup in production.
    """
    results = {
        "secrets": audit_environment_secrets(),
        "tls": check_tls_enforcement(),
        "s3_encryption": await check_s3_encryption(),
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
