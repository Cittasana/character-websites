"""
Unit tests for Claude analysis response parsing and validation.
Uses mocked Claude API responses — no real API calls.
"""
import json
import pytest

from app.analysis.claude_analysis import _parse_claude_response, _validate_schema


class TestParseClaudeResponse:
    def test_parses_valid_json(self) -> None:
        sample = {
            "dimensions": {
                "warmth": 75, "energy": 60, "confidence": 80,
                "curiosity": 70, "formality": 55, "humor": 40, "openness": 65
            },
            "persona_blend": {"primary": "minimalist-refined", "primary_weight": 70,
                              "secondary": "organic-warm", "secondary_weight": 30},
            "color_palette": {"temperature": "warm", "saturation": "medium", "accent": "#E8734A"},
            "typography": {"display_class": "geometric", "body_class": "humanist", "weight": "regular"},
            "layout": {"density": 4, "asymmetry": 6, "whitespace_ratio": 7, "flow_direction": "vertical"},
            "animation": {"speed": "medium", "intensity": "subtle"},
            "cv_content": {"tone": "balanced", "headline": "Strategic thinker", "summary": "Test", "key_strengths": []},
            "dating_content": {"tone": "warm", "opening_line": "Hi", "personality_highlight": "Curious", "conversation_starters": []},
        }
        result = _parse_claude_response(json.dumps(sample))
        assert result["dimensions"]["warmth"] == 75
        assert result["color_palette"]["accent"] == "#E8734A"

    def test_strips_markdown_code_fences(self) -> None:
        sample = {"dimensions": {"warmth": 60, "energy": 50, "confidence": 70,
                                  "curiosity": 55, "formality": 60, "humor": 35, "openness": 65},
                  "persona_blend": {"primary": "minimalist-refined", "primary_weight": 70,
                                    "secondary": "organic-warm", "secondary_weight": 30},
                  "color_palette": {"temperature": "cool", "saturation": "low", "accent": "#4A90E2"},
                  "typography": {"display_class": "serif", "body_class": "geometric", "weight": "light"},
                  "layout": {"density": 3, "asymmetry": 4, "whitespace_ratio": 8, "flow_direction": "vertical"},
                  "animation": {"speed": "slow", "intensity": "subtle"},
                  "cv_content": None, "dating_content": None}
        wrapped = f"```json\n{json.dumps(sample)}\n```"
        result = _parse_claude_response(wrapped)
        assert result["dimensions"]["warmth"] == 60

    def test_returns_fallback_on_invalid_json(self) -> None:
        result = _parse_claude_response("this is not json at all { broken")
        # Should return template defaults without raising
        assert "dimensions" in result
        assert "warmth" in result["dimensions"]

    def test_handles_missing_fields(self) -> None:
        # Partial schema — only dimensions
        partial = {"dimensions": {"warmth": 80}}
        result = _validate_schema(partial)
        # Missing fields should use defaults
        assert "color_palette" in result
        assert result["color_palette"]["accent"] == "#6B7280"


class TestValidateSchema:
    def test_clamps_dimension_values(self) -> None:
        sample = {"dimensions": {"warmth": 150, "energy": -10, "confidence": 50,
                                  "curiosity": 50, "formality": 50, "humor": 50, "openness": 50},
                  "persona_blend": {"primary": "minimalist-refined", "primary_weight": 70,
                                    "secondary": "organic-warm", "secondary_weight": 30},
                  "color_palette": {"temperature": "warm", "saturation": "medium", "accent": "#AABBCC"},
                  "typography": {"display_class": "serif", "body_class": "serif", "weight": "bold"},
                  "layout": {"density": 50, "asymmetry": -1, "whitespace_ratio": 5, "flow_direction": "vertical"},
                  "animation": {"speed": "fast", "intensity": "pronounced"},
                  "cv_content": None, "dating_content": None}
        result = _validate_schema(sample)
        assert result["dimensions"]["warmth"] == 100  # clamped from 150
        assert result["dimensions"]["energy"] == 0    # clamped from -10
        assert result["layout"]["density"] == 10       # clamped from 50
        assert result["layout"]["asymmetry"] == 1      # clamped from -1

    def test_rejects_invalid_accent_hex(self) -> None:
        sample = {"dimensions": {k: 50 for k in ["warmth", "energy", "confidence", "curiosity", "formality", "humor", "openness"]},
                  "persona_blend": {"primary": "minimalist-refined", "primary_weight": 70,
                                    "secondary": "organic-warm", "secondary_weight": 30},
                  "color_palette": {"temperature": "warm", "saturation": "medium", "accent": "invalid"},
                  "typography": {}, "layout": {}, "animation": {}, "cv_content": None, "dating_content": None}
        result = _validate_schema(sample)
        # Should fall back to default hex
        assert result["color_palette"]["accent"] == "#6B7280"

    def test_primary_weight_clamp(self) -> None:
        sample = {"dimensions": {k: 50 for k in ["warmth", "energy", "confidence", "curiosity", "formality", "humor", "openness"]},
                  "persona_blend": {"primary": "minimalist-refined", "primary_weight": 200,
                                    "secondary": "organic-warm", "secondary_weight": -100},
                  "color_palette": {"temperature": "neutral", "saturation": "medium", "accent": "#000000"},
                  "typography": {}, "layout": {}, "animation": {}, "cv_content": None, "dating_content": None}
        result = _validate_schema(sample)
        pw = result["persona_blend"]["primary_weight"]
        sw = result["persona_blend"]["secondary_weight"]
        assert 50 <= pw <= 85
        assert pw + sw == 100

    def test_invalid_persona_gets_default(self) -> None:
        sample = {"dimensions": {k: 50 for k in ["warmth", "energy", "confidence", "curiosity", "formality", "humor", "openness"]},
                  "persona_blend": {"primary": "nonexistent-persona", "primary_weight": 70,
                                    "secondary": "also-invalid", "secondary_weight": 30},
                  "color_palette": {"temperature": "neutral", "saturation": "medium", "accent": "#000000"},
                  "typography": {}, "layout": {}, "animation": {}, "cv_content": None, "dating_content": None}
        result = _validate_schema(sample)
        valid_personas = {
            "minimalist-refined", "organic-warm", "bold-expressive",
            "technical-precise", "playful-creative", "classic-authoritative"
        }
        assert result["persona_blend"]["primary"] in valid_personas
