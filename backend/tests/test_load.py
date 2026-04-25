"""
Load tests using locust for upload pipeline throughput and retrieve route latency.
Target: p99 response time <100ms for retrieve routes.

Run with:
    locust -f tests/test_load.py --host http://localhost:8000
"""
import json
import random
import uuid

import pytest
pytest.importorskip("locust")

from locust import HttpUser, TaskSet, between, task


class RetrieveTaskSet(TaskSet):
    """Retrieve route load tests."""

    def on_start(self) -> None:
        """Register and login to get auth token."""
        email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        password = "loadtestpass123"

        reg = self.client.post(
            "/api/auth/register",
            json={"email": email, "password": password},
        )
        if reg.status_code == 201:
            data = reg.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            # Extract user_id from token (decode without verify for load test)
            import base64
            payload_b64 = self.token.split(".")[1]
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.b64decode(padded))
            self.user_id = payload.get("sub", str(uuid.uuid4()))
        else:
            self.token = None
            self.headers = {}
            self.user_id = str(uuid.uuid4())

    @task(5)
    def get_health(self) -> None:
        with self.client.get("/health", catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()

    @task(3)
    def get_website_schema(self) -> None:
        if not self.token:
            return
        with self.client.get(
            f"/api/retrieve/website/{self.user_id}",
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()

    @task(3)
    def get_personality(self) -> None:
        if not self.token:
            return
        with self.client.get(
            f"/api/retrieve/personality/{self.user_id}",
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()

    @task(2)
    def get_voiceclips(self) -> None:
        if not self.token:
            return
        with self.client.get(
            f"/api/retrieve/voiceclips/{self.user_id}",
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()


class UploadTaskSet(TaskSet):
    """Upload route throughput tests."""

    def on_start(self) -> None:
        email = f"uploadtest_{uuid.uuid4().hex[:8]}@example.com"
        password = "uploadtestpass123"
        reg = self.client.post(
            "/api/auth/register",
            json={"email": email, "password": password},
        )
        if reg.status_code == 201:
            self.token = reg.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(1)
    def upload_transcript(self) -> None:
        if not self.token:
            return
        text = "This is a load test transcript. " * 20  # ~640 chars
        with self.client.post(
            "/api/upload/transcript",
            json={"transcript": text, "source": "manual"},
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code in (202, 429):  # 429 = rate limited, expected
                resp.success()


class RetrieveUser(HttpUser):
    """Simulates a user browsing personal websites (retrieve-heavy)."""
    tasks = [RetrieveTaskSet]
    wait_time = between(0.5, 2.0)
    weight = 8  # 80% of virtual users


class UploadUser(HttpUser):
    """Simulates a user uploading content."""
    tasks = [UploadTaskSet]
    wait_time = between(5, 15)
    weight = 2  # 20% of virtual users
