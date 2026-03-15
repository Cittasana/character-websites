"""
Full pipeline integration test.
Runs against real Supabase (yeiizwkinffsjtfmvjio).
Requires: SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY in env.
"""
import os, httpx, pytest
from supabase import create_client

SUPABASE_URL = "https://yeiizwkinffsjtfmvjio.supabase.co"
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.fixture
def supabase():
    return create_client(SUPABASE_URL, SERVICE_KEY)

def test_demo_user_exists(supabase):
    """Seed data: demo user should exist."""
    res = supabase.table("users").select("id,username").eq("username", "demo").execute()
    assert len(res.data) == 1
    assert res.data[0]["username"] == "demo"

def test_personality_schema_exists(supabase):
    """Demo user should have a current personality schema."""
    res = supabase.table("personality_schemas").select("*").eq("is_current", True).execute()
    assert len(res.data) >= 1
    schema = res.data[0]
    assert 0 <= schema["dim_warmth"] <= 100
    assert schema["primary_persona"] in ["minimalist-refined", "maximalist-bold", "organic-warm", "structured-professional"]

def test_get_website_data_rpc(supabase):
    """Helper function get_website_data should return full website data for 'demo'."""
    res = supabase.rpc("get_website_data", {"p_username": "demo"}).execute()
    assert res.data is not None
    data = res.data
    assert "user" in data
    assert "personality" in data
    assert data["user"]["username"] == "demo"
    assert "dim_warmth" in data["personality"]
    assert "primary_persona" in data["personality"]

def test_voice_clips_exist(supabase):
    """Demo user should have 3 voice clips seeded."""
    res = supabase.table("voice_clips").select("id,title,duration_seconds").execute()
    assert len(res.data) >= 3

def test_website_configs_exist(supabase):
    """Demo user should have cv and dating configs."""
    res = supabase.table("website_configs").select("mode,is_published").execute()
    modes = {c["mode"] for c in res.data}
    assert "cv" in modes
    assert "dating" in modes

def test_storage_buckets_exist(supabase):
    """All 3 storage buckets should exist."""
    buckets = supabase.storage.list_buckets()
    bucket_names = {b.name for b in buckets}
    assert "voice-recordings" in bucket_names
    assert "user-photos" in bucket_names
    assert "voice-clips" in bucket_names
