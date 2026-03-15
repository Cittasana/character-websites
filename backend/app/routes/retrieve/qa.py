"""
POST /api/retrieve/qa
Employer Q&A endpoint — receives a question and generates a response
in the user's communication style (derived from personality analysis).
Returns answer text + TTS-ready content.
Read-only. Session validation required.
"""
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.supabase_client import get_supabase

settings = get_settings()
router = APIRouter(prefix="/api/retrieve", tags=["retrieve"])
limiter = Limiter(key_func=get_remote_address)


class QARequest(BaseModel):
    user_id: uuid.UUID
    question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="The employer's question",
    )


class QAResponse(BaseModel):
    user_id: uuid.UUID
    question: str
    answer: str
    tts_content: dict[str, Any]
    communication_style: dict[str, Any]


_QA_SYSTEM_PROMPT = """You are generating a response on behalf of a professional job candidate.
Your response MUST match their personality and communication style precisely.
The response should sound authentic and personal — not generic.
Keep answers concise (2-4 sentences unless the question demands more).
Do NOT include meta-commentary or explain your reasoning."""

_QA_PROMPT_TEMPLATE = """Generate a response to this employer question on behalf of the candidate.

CANDIDATE PERSONALITY PROFILE:
- Warmth: {warmth}/100, Energy: {energy}/100, Confidence: {confidence}/100
- Curiosity: {curiosity}/100, Formality: {formality}/100, Humor: {humor}/100
- Openness: {openness}/100
- Primary persona: {primary_persona} ({primary_weight}%)
- Secondary persona: {secondary_persona} ({secondary_weight}%)

EMPLOYER QUESTION:
{question}

CV CONTEXT (if available):
{cv_context}

Write the response in the candidate's authentic voice. Match their formality level exactly.
If humor > 60, allow one light touch of wit. If formality > 70, keep it professional.
Return ONLY the response text — no labels, no quotes."""


@router.post(
    "/qa",
    response_model=QAResponse,
    summary="Generate employer Q&A response in user's voice",
    description=(
        "Receives a question and generates a Claude-powered response "
        "in the user's authentic communication style. "
        "Returns text + TTS-ready metadata. JWT required."
    ),
)
@limiter.limit("60/hour")  # stricter limit for AI-powered endpoint
async def answer_employer_question(
    request: Request,
    body: QARequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> QAResponse:
    # Only the user themselves can generate Q&A responses (their own voice)
    if str(current_user.id) != str(body.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # ── Load personality schema ───────────────────────────────────────────
    supabase = get_supabase()
    result = supabase.table("personality_schemas").select("*").eq(
        "user_id", str(body.user_id)
    ).eq("is_current", True).order("created_at", desc=True).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No personality profile found. Upload a voice recording first.",
        )

    schema = result.data[0]
    dims = schema.get("dimensions", {})
    blend = schema.get("persona_blend", {})
    cv = schema.get("cv_content") or {}

    cv_context = ""
    if cv:
        summary = cv.get("summary", "")
        strengths = ", ".join(cv.get("key_strengths", []))
        if summary:
            cv_context = f"Professional summary: {summary}"
        if strengths:
            cv_context += f"\nKey strengths: {strengths}"

    prompt = _QA_PROMPT_TEMPLATE.format(
        warmth=dims.get("warmth", 50),
        energy=dims.get("energy", 50),
        confidence=dims.get("confidence", 50),
        curiosity=dims.get("curiosity", 50),
        formality=dims.get("formality", 50),
        humor=dims.get("humor", 50),
        openness=dims.get("openness", 50),
        primary_persona=blend.get("primary", "professional"),
        primary_weight=blend.get("primary_weight", 70),
        secondary_persona=blend.get("secondary", "warm"),
        secondary_weight=blend.get("secondary_weight", 30),
        question=body.question,
        cv_context=cv_context or "Not provided",
    )

    # ── Call Claude ───────────────────────────────────────────────────────
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=512,
        system=_QA_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    answer_text = message.content[0].text.strip()

    # ── Build TTS metadata ────────────────────────────────────────────────
    energy = dims.get("energy", 50)
    formality = dims.get("formality", 50)

    tts_content = {
        "text": answer_text,
        "speaking_rate": _map_to_tts_rate(energy),
        "pitch": _map_to_tts_pitch(dims.get("warmth", 50)),
        "volume_gain_db": 0.0,
        "voice_style": "formal" if formality > 65 else "conversational",
        "pause_after_sentences_ms": 400 if formality > 65 else 250,
    }

    communication_style = {
        "formality_level": "formal" if formality > 70 else "semi-formal" if formality > 40 else "casual",
        "energy_level": "high" if energy > 70 else "medium" if energy > 40 else "low",
        "primary_persona": blend.get("primary"),
    }

    return QAResponse(
        user_id=body.user_id,
        question=body.question,
        answer=answer_text,
        tts_content=tts_content,
        communication_style=communication_style,
    )


def _map_to_tts_rate(energy: int) -> float:
    """Map energy (0-100) to TTS speaking rate (0.7–1.3x)."""
    return round(0.7 + (energy / 100) * 0.6, 2)


def _map_to_tts_pitch(warmth: int) -> float:
    """Map warmth (0-100) to TTS pitch shift (-2 to +2 semitones)."""
    return round(-2.0 + (warmth / 100) * 4.0, 2)
