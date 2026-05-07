"""Frozen Layer-T and Layer-M prompts. v0.1.0 does NOT call an LLM."""
from __future__ import annotations

LAYER_T_ENROLMENT_PROMPT = (
    "You are a clinical-trial epidemiologist. Given the verbatim primary-publication "
    "excerpt below, extract per-country enrolment counts as JSON: "
    "{\"by_country\": {\"South Africa\": 700, ...}, \"total\": 3224, "
    "\"flags\": [\"ambiguous\"|\"negation\"|\"multi_match\"]}. "
    "Only include African countries (54-country UN list). If the excerpt does NOT "
    "specify a count for a country, omit it — never guess.\n\nEXCERPT:\n"
)

LAYER_M_NARRATIVE_PROMPT = (
    "Given the meta-analysis discussion paragraph below and a target trial id, "
    "decide whether the paragraph mentions this trial in an Africa-related context. "
    "Return JSON: {\"trial_id\": \"...\", \"africa_context\": true|false, "
    "\"verbatim_quote\": \"...\", \"flags\": []}. "
    "africa_context is true only if the paragraph names the trial AND an African "
    "country/region/population in the same sentence.\n\nPARAGRAPH:\n"
)

# SHA256 pins. After editing the strings above, regenerate via:
#   python -c "import hashlib; from africa_hiv_prep_atlas import llm_prompts as m; \
#     print(hashlib.sha256(m.LAYER_T_ENROLMENT_PROMPT.encode()).hexdigest()); \
#     print(hashlib.sha256(m.LAYER_M_NARRATIVE_PROMPT.encode()).hexdigest())"
LAYER_T_ENROLMENT_PROMPT_SHA256 = "15adca979d2b441a87ee69c3841fecf35da300f6b7ce7f7c107913ab5b605ef4"
LAYER_M_NARRATIVE_PROMPT_SHA256 = "b88238ebed59b6e567c08f67f648bff8767ddfa7b00ef40bb1a8d7a19af0a578"
