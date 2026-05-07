"""Unit tests for frozen LLM prompts with SHA256 pins."""
import hashlib

from africa_hiv_prep_atlas.llm_prompts import (
    LAYER_T_ENROLMENT_PROMPT,
    LAYER_T_ENROLMENT_PROMPT_SHA256,
    LAYER_M_NARRATIVE_PROMPT,
    LAYER_M_NARRATIVE_PROMPT_SHA256,
)


def test_layer_t_prompt_pinned_to_sha():
    actual = hashlib.sha256(LAYER_T_ENROLMENT_PROMPT.encode("utf-8")).hexdigest()
    assert actual == LAYER_T_ENROLMENT_PROMPT_SHA256


def test_layer_m_prompt_pinned_to_sha():
    actual = hashlib.sha256(LAYER_M_NARRATIVE_PROMPT.encode("utf-8")).hexdigest()
    assert actual == LAYER_M_NARRATIVE_PROMPT_SHA256


def test_layer_t_prompt_mentions_african_enrolment():
    assert "African" in LAYER_T_ENROLMENT_PROMPT
    assert "enrolment" in LAYER_T_ENROLMENT_PROMPT.lower() or "enrolled" in LAYER_T_ENROLMENT_PROMPT.lower()


def test_layer_m_prompt_returns_structured_json():
    assert "JSON" in LAYER_M_NARRATIVE_PROMPT
