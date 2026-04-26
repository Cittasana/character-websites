"""
Onboarding: first user chooses public username and gets a starter personality + website config.
Uses service-role Supabase for inserts (RLS has no user-level insert on personality_schemas).
"""
from __future__ import annotations

import re
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.auth.dependencies import get_current_active_user
from app.supabase_client import get_supabase

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

USERNAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,28}[a-z0-9]$")
RESERVED_PREFIX = "cwtmp_"


class OnboardingStatusResponse(BaseModel):
    needs_onboarding: bool
    username: str
    display_name: str | None


class OnboardingCompleteRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    display_name: str = Field(..., min_length=1, max_length=120)

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        s = v.strip().lower()
        if not USERNAME_RE.match(s):
            raise ValueError(
                "Username must be 3–30 characters, lowercase letters, numbers, "
                "single hyphens inside, and start with a letter."
            )
        if s.startswith(RESERVED_PREFIX):
            raise ValueError("This username is reserved.")
        return s

    @field_validator("display_name")
    @classmethod
    def display_trim(cls, v: str) -> str:
        return v.strip()


class OnboardingCompleteResponse(BaseModel):
    ok: bool
    username: str


def _starter_cv_content(display_name: str) -> dict[str, Any]:
    return {
        "headline": f"Willkommen, {display_name}",
        "positioning_statement": (
            "Hier entsteht deine Character Website — füge Stimme, Fotos und "
            "Alltag hinzu, damit sich das Profil mit dir weiterentwickelt."
        ),
        "summary": "",
        "work_history": [],
        "skills": [],
        "education": [],
        "languages": [],
    }


def _starter_dating_content(display_name: str) -> dict[str, Any]:
    return {
        "tagline": f"Hey, ich bin {display_name}",
        "intro": (
            "Dieses Profil wächst mit deinen Aufnahmen und Antworten. "
            "Starte mit einer kurzen Voice-Notiz oder einem Foto."
        ),
        "values": [],
        "looking_for": [],
        "personality_tagline": "Neu hier — neugierig und authentisch.",
        "interests": [],
        "ambition_score": 5,
        "adventure_score": 5,
    }


@router.get("/status", response_model=OnboardingStatusResponse)
async def onboarding_status(
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> OnboardingStatusResponse:
    supabase = get_supabase()
    uid = str(current_user.id)

    user_res = (
        supabase.table("users")
        .select("username, display_name")
        .eq("id", uid)
        .single()
        .execute()
    )
    if not user_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    username = user_res.data.get("username") or ""
    display_name = user_res.data.get("display_name")

    ps = (
        supabase.table("personality_schemas")
        .select("id")
        .eq("user_id", uid)
        .eq("is_current", True)
        .limit(1)
        .execute()
    )
    needs = not (ps.data and len(ps.data) > 0)
    return OnboardingStatusResponse(
        needs_onboarding=needs,
        username=username,
        display_name=display_name,
    )


@router.post("/complete", response_model=OnboardingCompleteResponse)
async def onboarding_complete(
    body: OnboardingCompleteRequest,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> OnboardingCompleteResponse:
    supabase = get_supabase()
    uid = str(current_user.id)

    clash = (
        supabase.table("users")
        .select("id")
        .eq("username", body.username)
        .limit(1)
        .execute()
    )
    if clash.data and str(clash.data[0].get("id")) != uid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken",
        )

    ps_check = (
        supabase.table("personality_schemas")
        .select("id")
        .eq("user_id", uid)
        .eq("is_current", True)
        .limit(1)
        .execute()
    )
    if ps_check.data and len(ps_check.data) > 0:
        supabase.table("users").update(
            {
                "username": body.username,
                "display_name": body.display_name,
            }
        ).eq("id", uid).execute()
        return OnboardingCompleteResponse(ok=True, username=body.username)

    schema_insert: dict[str, Any] = {
        "user_id": uid,
        "version": 1,
        "is_current": True,
        "dim_warmth": 58,
        "dim_energy": 55,
        "dim_confidence": 60,
        "dim_curiosity": 62,
        "dim_formality": 45,
        "dim_humor": 55,
        "dim_openness": 65,
        "primary_persona": "organic-warm",
        "primary_weight": 70,
        "secondary_persona": "minimalist-refined",
        "secondary_weight": 30,
        "color_temperature": "warm",
        "color_saturation": "medium",
        "color_accent": "#e07a5f",
        "typography_display": "humanist",
        "typography_body": "humanist",
        "typography_weight": "regular",
        "layout_density": 5,
        "layout_asymmetry": 4,
        "layout_whitespace": 6,
        "layout_flow": "vertical",
        "animation_speed": "medium",
        "animation_intensity": "moderate",
        "cv_content": _starter_cv_content(body.display_name),
        "dating_content": _starter_dating_content(body.display_name),
    }

    ins = supabase.table("personality_schemas").insert(schema_insert).execute()
    if not ins.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create personality schema",
        )
    schema_id = ins.data[0]["id"]

    supabase.table("users").update(
        {
            "username": body.username,
            "display_name": body.display_name,
        }
    ).eq("id", uid).execute()

    supabase.table("website_configs").insert(
        {
            "user_id": uid,
            "schema_id": schema_id,
            "mode": "cv",
            "is_published": True,
        }
    ).execute()

    try:
        supabase.table("audit_logs").insert(
            {
                "user_id": uid,
                "event_type": "onboarding.complete",
                "resource_type": "user",
                "resource_id": uid,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "metadata": {"username": body.username},
            }
        ).execute()
    except Exception:
        pass

    return OnboardingCompleteResponse(ok=True, username=body.username)
