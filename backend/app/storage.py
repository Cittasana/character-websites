"""
Supabase Storage service.
Replaces the old boto3/S3 storage client.
Buckets: voice-recordings, user-photos, voice-clips
"""
from supabase import Client

from app.supabase_client import get_supabase


class StorageService:
    def __init__(self, client: Client):
        self.client = client

    def upload_voice(
        self,
        user_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        """
        Upload to voice-recordings bucket.
        Returns the storage path (user_id/filename).
        """
        path = f"{user_id}/{filename}"
        self.client.storage.from_("voice-recordings").upload(
            path,
            file_bytes,
            {"content-type": content_type, "upsert": "false"},
        )
        return path

    def upload_photo(
        self,
        user_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        """
        Upload to user-photos bucket.
        Returns the storage path (user_id/filename).
        """
        path = f"{user_id}/{filename}"
        self.client.storage.from_("user-photos").upload(
            path,
            file_bytes,
            {"content-type": content_type, "upsert": "false"},
        )
        return path

    def upload_voice_clip(
        self,
        user_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        """
        Upload to voice-clips bucket.
        Returns the storage path.
        """
        path = f"{user_id}/{filename}"
        self.client.storage.from_("voice-clips").upload(
            path,
            file_bytes,
            {"content-type": content_type, "upsert": "false"},
        )
        return path

    def get_signed_url(self, bucket: str, path: str, expires_in: int = 3600) -> str:
        """Generate a signed URL for private file access. Default expiry: 1 hour."""
        response = self.client.storage.from_(bucket).create_signed_url(path, expires_in)
        return response["signedURL"]

    def download(self, bucket: str, path: str) -> bytes:
        """Download a file from Supabase Storage and return its bytes."""
        return self.client.storage.from_(bucket).download(path)

    def delete_file(self, bucket: str, path: str) -> None:
        """Delete a file from the given bucket."""
        self.client.storage.from_(bucket).remove([path])


def get_storage_service() -> StorageService:
    """Factory — returns a StorageService backed by the service-role client."""
    return StorageService(get_supabase())
