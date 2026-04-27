"""
Claude AI personality analysis.
Sends transcript + acoustic metadata to Claude claude-sonnet-4-20250514,
gets back structured JSON personality schema.

Rate-limit aware:
- Honours the ``retry-after`` header on Anthropic 429/529 responses by
  sleeping the requested amount (capped) before letting tenacity retry.
- Global RPM throttling is owned by the Celery worker layer
  (``app.jobs.rate_limiter.acquire_global_token``), not this module.
"""
import asyncio
import json
import logging
import re
from typing import Any

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Cap retry-after waits so a misconfigured upstream cannot hang the worker
# for hours.
_MAX_RETRY_AFTER_SECONDS = 60.0

# ── Structured response schema ─────────────────────────────────────────────────
PERSONALITY_SCHEMA_TEMPLATE = {
    "dimensions": {
        "warmth": 0,
        "energy": 0,
        "confidence": 0,
        "curiosity": 0,
        "formality": 0,
        "humor": 0,
        "openness": 0,
    },
    "persona_blend": {
        "primary": "minimalist-refined",
        "primary_weight": 70,
        "secondary": "organic-warm",
        "secondary_weight": 30,
    },
    "color_palette": {
        "temperature": "neutral",
        "saturation": "medium",
        "accent": "#6B7280",
    },
    "typography": {
        "display_class": "geometric",
        "body_class": "humanist",
        "weight": "regular",
    },
    "layout": {
        "density": 5,
        "asymmetry": 5,
        "whitespace_ratio": 5,
        "flow_direction": "vertical",
    },
    "animation": {
        "speed": "medium",
        "intensity": "subtle",
    },
    "cv_content": {
        "tone": "professional",
        "headline": "",
        "summary": "",
        "key_strengths": [],
    },
    "dating_content": {
        "tone": "warm",
        "opening_line": "",
        "personality_highlight": "",
        "conversation_starters": [],
    },
}

_SYSTEM_PROMPT = """You are a personality analyst and design system AI for Character-Websites.
Your task is to analyze voice transcript data and acoustic metadata to produce a precise,
structured personality profile that drives the visual design of a personal website.

Be specific, nuanced, and grounded in the evidence. Do not invent traits not supported
by the data. Every dimension score should reflect genuine signal from the transcript
and acoustic features.

You MUST respond with valid JSON only — no prose, no markdown, no code fences."""

_USER_PROMPT_TEMPLATE = """Analyze the following voice transcript and acoustic data.
Return a JSON object matching EXACTLY the schema below.

--- TRANSCRIPT ---
{transcript}

--- ACOUSTIC DATA ---
{acoustic_summary}

--- REQUIRED JSON SCHEMA ---
{{
  "dimensions": {{
    "warmth": <0-100 integer, evidence from language warmth/empathy>,
    "energy": <0-100 integer, derived from pacing + vocal energy>,
    "confidence": <0-100 integer, from declarative statements, low hedging>,
    "curiosity": <0-100 integer, from question frequency, exploratory language>,
    "formality": <0-100 integer, from register, vocabulary complexity>,
    "humor": <0-100 integer, from wordplay, levity, wit>,
    "openness": <0-100 integer, from abstract thinking, hypotheticals>
  }},
  "persona_blend": {{
    "primary": "<one of: minimalist-refined | organic-warm | bold-expressive | technical-precise | playful-creative | classic-authoritative>",
    "primary_weight": <50-85 integer>,
    "secondary": "<different persona from the list above>",
    "secondary_weight": <15-50 integer, must sum to 100 with primary_weight>
  }},
  "color_palette": {{
    "temperature": "<warm | cool | neutral>",
    "saturation": "<high | medium | low>",
    "accent": "<hex color that fits the personality, e.g. #E8734A>"
  }},
  "typography": {{
    "display_class": "<serif | geometric | humanist | modern-sans>",
    "body_class": "<serif | geometric | humanist | modern-sans>",
    "weight": "<light | regular | bold>"
  }},
  "layout": {{
    "density": <1-10, 1=minimal, 10=dense>,
    "asymmetry": <1-10, 1=rigid, 10=fluid>,
    "whitespace_ratio": <1-10, 1=packed, 10=airy>,
    "flow_direction": "<vertical | horizontal | diagonal>"
  }},
  "animation": {{
    "speed": "<slow | medium | fast>",
    "intensity": "<subtle | moderate | pronounced>"
  }},
  "cv_content": {{
    "tone": "<conservative | balanced | creative>",
    "headline": "<compelling 10-word professional headline derived from the transcript>",
    "summary": "<3-sentence professional summary in the speaker's voice>",
    "key_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"]
  }},
  "dating_content": {{
    "tone": "<warm | playful | intellectual | adventurous>",
    "opening_line": "<authentic 1-2 sentence opening for a dating profile>",
    "personality_highlight": "<1 sentence that captures the most distinctive quality>",
    "conversation_starters": ["<topic 1>", "<topic 2>", "<topic 3>"]
  }}
}}

Respond with ONLY the JSON object. No explanation, no markdown formatting."""


def _retry_on_anthropic_transient_errors(exc: BaseException) -> bool:
    """
    Retry policy for tenacity: only retry on transient Anthropic conditions
    (rate limits, overloaded, timeouts, transient API errors). Validation
    errors / auth errors should fail fast.
    """
    import anthropic

    return isinstance(
        exc,
        (
            anthropic.RateLimitError,
            anthropic.APIConnectionError,
            anthropic.APITimeoutError,
            anthropic.InternalServerError,
        ),
    )


def _extract_retry_after_seconds(exc: BaseException) -> float | None:
    """Read ``retry-after`` header (seconds) from an Anthropic exception."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    raw = headers.get("retry-after") or headers.get("Retry-After")
    if not raw:
        return None
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(_MAX_RETRY_AFTER_SECONDS, seconds))


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception(_retry_on_anthropic_transient_errors),
    reraise=True,
)
async def analyze_personality_with_claude(
    transcript: str,
    acoustic_summary: str,
) -> dict[str, Any]:
    """
    Send transcript and acoustic data to Claude and get structured personality schema.

    Retries up to 3 times with exponential backoff on transient errors.
    On 429 / 529, honours Anthropic's ``retry-after`` header before letting
    tenacity decide whether to retry.
    """
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = _USER_PROMPT_TEMPLATE.format(
        transcript=transcript[:10_000],  # truncate to avoid token limit issues
        acoustic_summary=acoustic_summary,
    )

    try:
        message = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.RateLimitError as exc:
        retry_after = _extract_retry_after_seconds(exc)
        if retry_after is not None:
            logger.warning(
                "Anthropic 429 — honouring retry-after=%.1fs before retry", retry_after,
            )
            await asyncio.sleep(retry_after)
        raise
    except anthropic.InternalServerError as exc:
        # 529 (Overloaded) also lands here in some SDK versions.
        retry_after = _extract_retry_after_seconds(exc)
        if retry_after is not None:
            logger.warning(
                "Anthropic overloaded — honouring retry-after=%.1fs before retry",
                retry_after,
            )
            await asyncio.sleep(retry_after)
        raise

    raw_response = message.content[0].text.strip()

    # ── Parse JSON response ───────────────────────────────────────────────
    parsed = _parse_claude_response(raw_response)
    return parsed, raw_response  # type: ignore


def _parse_claude_response(raw_text: str) -> dict[str, Any]:
    """
    Robustly parse JSON from Claude's response.
    Handles cases where the model wraps JSON in markdown fences.
    """
    # Strip markdown code fences if present
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Claude JSON response: %s\nRaw: %s", exc, raw_text[:500])
        # Return a fallback schema
        return dict(PERSONALITY_SCHEMA_TEMPLATE)

    # ── Validate and sanitize ─────────────────────────────────────────────
    return _validate_schema(parsed)


def _validate_schema(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and clamp personality schema values to expected ranges.
    Falls back to defaults for missing or invalid fields.
    """
    template = dict(PERSONALITY_SCHEMA_TEMPLATE)

    # Validate dimensions (0-100 integers)
    dims = data.get("dimensions", {})
    validated_dims = {}
    for key in template["dimensions"]:
        val = dims.get(key, 50)
        try:
            validated_dims[key] = max(0, min(100, int(val)))
        except (TypeError, ValueError):
            validated_dims[key] = 50

    # Validate persona_blend
    valid_personas = {
        "minimalist-refined", "organic-warm", "bold-expressive",
        "technical-precise", "playful-creative", "classic-authoritative",
    }
    blend = data.get("persona_blend", {})
    primary = blend.get("primary", "minimalist-refined")
    secondary = blend.get("secondary", "organic-warm")
    if primary not in valid_personas:
        primary = "minimalist-refined"
    if secondary not in valid_personas or secondary == primary:
        # pick a different default
        secondary = next(p for p in valid_personas if p != primary)
    try:
        pw = max(50, min(85, int(blend.get("primary_weight", 70))))
        sw = 100 - pw
    except (TypeError, ValueError):
        pw, sw = 70, 30

    # Validate color palette
    palette = data.get("color_palette", {})
    accent = palette.get("accent", "#6B7280")
    if not re.match(r"^#[0-9A-Fa-f]{6}$", str(accent)):
        accent = "#6B7280"

    # Validate layout (1-10 integers)
    layout = data.get("layout", {})
    validated_layout = {}
    for key in ["density", "asymmetry", "whitespace_ratio"]:
        try:
            validated_layout[key] = max(1, min(10, int(layout.get(key, 5))))
        except (TypeError, ValueError):
            validated_layout[key] = 5
    flow = layout.get("flow_direction", "vertical")
    validated_layout["flow_direction"] = flow if flow in ("vertical", "horizontal", "diagonal") else "vertical"

    return {
        "dimensions": validated_dims,
        "persona_blend": {
            "primary": primary,
            "primary_weight": pw,
            "secondary": secondary,
            "secondary_weight": sw,
        },
        "color_palette": {
            "temperature": palette.get("temperature", "neutral")
            if palette.get("temperature") in ("warm", "cool", "neutral") else "neutral",
            "saturation": palette.get("saturation", "medium")
            if palette.get("saturation") in ("high", "medium", "low") else "medium",
            "accent": accent,
        },
        "typography": {
            "display_class": data.get("typography", {}).get("display_class", "geometric"),
            "body_class": data.get("typography", {}).get("body_class", "humanist"),
            "weight": data.get("typography", {}).get("weight", "regular"),
        },
        "layout": validated_layout,
        "animation": {
            "speed": data.get("animation", {}).get("speed", "medium"),
            "intensity": data.get("animation", {}).get("intensity", "subtle"),
        },
        "cv_content": data.get("cv_content", template["cv_content"]),
        "dating_content": data.get("dating_content", template["dating_content"]),
    }
