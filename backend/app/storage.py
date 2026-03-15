"""
S3-compatible object storage client.
Handles upload, signed URL generation, and server-side encryption validation.
"""
import uuid
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()


def _get_s3_client():
    """Build boto3 S3 client from environment config."""
    kwargs = {
        "region_name": settings.S3_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    }
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def _build_s3_key(user_id: str, file_type: str, original_filename: str) -> str:
    """
    Build a deterministic, collision-resistant S3 key.
    Format: {file_type}/{user_id}/{uuid4}.{ext}
    """
    ext = Path(original_filename).suffix.lower()
    return f"{file_type}/{user_id}/{uuid.uuid4()}{ext}"


def upload_file_to_s3(
    file_obj: BinaryIO,
    user_id: str,
    file_type: str,  # 'voice' | 'photo' | 'voice_clip'
    original_filename: str,
    content_type: str,
    bucket: str | None = None,
) -> dict[str, str]:
    """
    Upload a file object to S3 with server-side encryption (AES-256).
    Returns {'s3_key': ..., 's3_bucket': ...}.
    """
    client = _get_s3_client()
    bucket_name = bucket or settings.S3_BUCKET_NAME
    s3_key = _build_s3_key(user_id, file_type, original_filename)

    client.upload_fileobj(
        file_obj,
        bucket_name,
        s3_key,
        ExtraArgs={
            "ContentType": content_type,
            "ServerSideEncryption": "AES256",  # enforce encryption at rest
            "Metadata": {
                "user-id": user_id,
                "original-filename": original_filename,
            },
        },
    )

    return {"s3_key": s3_key, "s3_bucket": bucket_name}


def generate_presigned_url(
    s3_key: str,
    bucket: str | None = None,
    expiry: int | None = None,
) -> str:
    """
    Generate a time-limited presigned GET URL for a private S3 object.
    Default expiry: 1 hour (3600 seconds).
    """
    client = _get_s3_client()
    bucket_name = bucket or settings.S3_BUCKET_NAME
    expiry_seconds = expiry or settings.S3_SIGNED_URL_EXPIRY

    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
    return url


def verify_bucket_encryption(bucket: str | None = None) -> bool:
    """
    Verify that the S3 bucket has server-side encryption enabled.
    Used in security hardening checks.
    """
    client = _get_s3_client()
    bucket_name = bucket or settings.S3_BUCKET_NAME
    try:
        response = client.get_bucket_encryption(Bucket=bucket_name)
        rules = (
            response.get("ServerSideEncryptionConfiguration", {})
            .get("Rules", [])
        )
        for rule in rules:
            sse = rule.get("ApplyServerSideEncryptionByDefault", {})
            if sse.get("SSEAlgorithm") in ("AES256", "aws:kms"):
                return True
        return False
    except ClientError as e:
        if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
            return False
        raise


def delete_object(s3_key: str, bucket: str | None = None) -> None:
    """Delete an object from S3 (used when upload fails mid-transaction)."""
    client = _get_s3_client()
    bucket_name = bucket or settings.S3_BUCKET_NAME
    client.delete_object(Bucket=bucket_name, Key=s3_key)
