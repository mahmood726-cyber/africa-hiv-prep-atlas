"""
Test suite for MA (meta-analysis) fixtures.

Validates schema and attribution of meta-analysis JSONs under fixtures/mas/.
Each MA directory must contain meta.json and claims.json.
Tests skip gracefully when fixtures are not yet populated (Task 14 USER ACTION pending).
"""

import json
from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "mas"


def _ma_dirs():
    """Return sorted list of MA fixture directories."""
    if not FIXTURE_DIR.exists():
        return []
    return sorted(p for p in FIXTURE_DIR.iterdir() if p.is_dir())


def test_at_least_10_mas():
    """Require at least 10 MA fixture directories."""
    ma_dirs = _ma_dirs()
    if not ma_dirs:
        pytest.skip(
            "USER ACTION pending: populate fixtures/mas/ with ≥10 LA-PrEP MA dirs "
            "(each with meta.json + claims.json). See docs/fixture_seeding_protocol.md"
        )
    assert len(ma_dirs) >= 10, f"Expected ≥10 MA dirs, got {len(ma_dirs)}"


def test_at_least_50_pairs_total():
    """Require at least 50 (MA, trial) pairs across all MAs."""
    ma_dirs = _ma_dirs()
    if not ma_dirs:
        pytest.skip(
            "USER ACTION pending: populate fixtures/mas/ with ≥10 LA-PrEP MA dirs "
            "to generate ≥50 (MA, trial) pairs. See docs/fixture_seeding_protocol.md"
        )
    total_pairs = 0
    for ma_dir in ma_dirs:
        claims_file = ma_dir / "claims.json"
        if claims_file.exists():
            with open(claims_file) as f:
                claims = json.load(f)
            total_pairs += len(claims.get("claims", {}))
    assert total_pairs >= 50, f"Expected ≥50 (MA, trial) pairs, got {total_pairs}"


def test_each_ma_dir_has_meta_and_claims():
    """Each MA directory must contain both meta.json and claims.json."""
    for ma_dir in _ma_dirs():
        meta_file = ma_dir / "meta.json"
        claims_file = ma_dir / "claims.json"
        assert meta_file.exists(), f"{ma_dir.name}: missing meta.json"
        assert claims_file.exists(), f"{ma_dir.name}: missing claims.json"


def test_meta_json_has_required_keys():
    """Each meta.json must have all required keys."""
    required_keys = {
        "ma_id", "first_author", "year", "doi", "pmid",
        "search_date", "cited_trial_ids", "full_text_source_id",
        "search_strategy_excerpt"
    }
    for ma_dir in _ma_dirs():
        meta_file = ma_dir / "meta.json"
        if not meta_file.exists():
            continue
        with open(meta_file) as f:
            meta = json.load(f)
        missing = required_keys - set(meta.keys())
        assert not missing, (
            f"{ma_dir.name}/meta.json: missing keys {missing}"
        )
        # Verify types
        assert isinstance(meta["ma_id"], str)
        assert isinstance(meta["first_author"], str)
        assert isinstance(meta["year"], int)
        assert isinstance(meta["doi"], str)
        assert isinstance(meta["pmid"], str)
        assert isinstance(meta["search_date"], str)
        assert isinstance(meta["cited_trial_ids"], list)
        assert isinstance(meta["full_text_source_id"], str)
        assert isinstance(meta["search_strategy_excerpt"], dict)


def test_search_strategy_excerpt_has_required_fields():
    """search_strategy_excerpt in meta.json must have source_id, locator, text."""
    required_fields = {"source_id", "locator", "text"}
    for ma_dir in _ma_dirs():
        meta_file = ma_dir / "meta.json"
        if not meta_file.exists():
            continue
        with open(meta_file) as f:
            meta = json.load(f)
        excerpt = meta.get("search_strategy_excerpt", {})
        missing = required_fields - set(excerpt.keys())
        assert not missing, (
            f"{ma_dir.name}/meta.json search_strategy_excerpt: missing {missing}"
        )
        assert isinstance(excerpt["text"], str) and excerpt["text"].strip(), (
            f"{ma_dir.name}: search_strategy_excerpt.text is empty or not a string"
        )


def test_claims_json_structure():
    """Each claims.json must have ma_id and claims dict with required structure."""
    for ma_dir in _ma_dirs():
        claims_file = ma_dir / "claims.json"
        if not claims_file.exists():
            continue
        with open(claims_file) as f:
            claims_doc = json.load(f)
        assert "ma_id" in claims_doc, (
            f"{ma_dir.name}/claims.json: missing ma_id"
        )
        assert "claims" in claims_doc, (
            f"{ma_dir.name}/claims.json: missing claims"
        )
        assert isinstance(claims_doc["claims"], dict), (
            f"{ma_dir.name}/claims.json: claims is not a dict"
        )


def test_each_trial_claim_has_boolean_layers():
    """Each trial in claims must have a, b, c boolean flags."""
    for ma_dir in _ma_dirs():
        claims_file = ma_dir / "claims.json"
        if not claims_file.exists():
            continue
        with open(claims_file) as f:
            claims_doc = json.load(f)
        for trial_id, trial_claim in claims_doc.get("claims", {}).items():
            for layer in ("a", "b", "c"):
                assert layer in trial_claim, (
                    f"{ma_dir.name}: trial {trial_id} missing layer '{layer}'"
                )
                assert isinstance(trial_claim[layer], bool), (
                    f"{ma_dir.name}: trial {trial_id} layer '{layer}' is not bool"
                )


def test_each_true_claim_backed_by_verbatim_quote():
    """For each TRUE boolean claim, there must be at least one verbatim_quotes entry."""
    for ma_dir in _ma_dirs():
        claims_file = ma_dir / "claims.json"
        if not claims_file.exists():
            continue
        with open(claims_file) as f:
            claims_doc = json.load(f)
        for trial_id, trial_claim in claims_doc.get("claims", {}).items():
            for layer in ("a", "b", "c"):
                if trial_claim.get(layer) is True:
                    # Must have at least one verbatim_quotes entry
                    verbatim_quotes = trial_claim.get("verbatim_quotes", [])
                    assert isinstance(verbatim_quotes, list) and len(verbatim_quotes) > 0, (
                        f"{ma_dir.name}: trial {trial_id} layer '{layer}' is TRUE "
                        f"but has no verbatim_quotes"
                    )
                    for i, quote in enumerate(verbatim_quotes):
                        assert "source_id" in quote and "text" in quote, (
                            f"{ma_dir.name}: trial {trial_id} quote {i} missing "
                            f"source_id or text"
                        )
                        assert isinstance(quote["text"], str) and quote["text"].strip(), (
                            f"{ma_dir.name}: trial {trial_id} quote {i} text empty"
                        )


def test_cited_trial_ids_present_in_trial_fixtures():
    """Each trial cited in meta.json must correspond to a fixture (Task 13 cross-check)."""
    # Read trial fixtures
    trial_fixture_dir = Path(__file__).parent.parent / "fixtures" / "trials"
    trial_ids = set()
    if trial_fixture_dir.exists():
        trial_ids = {f.stem for f in trial_fixture_dir.glob("*.json")}

    for ma_dir in _ma_dirs():
        meta_file = ma_dir / "meta.json"
        if not meta_file.exists():
            continue
        with open(meta_file) as f:
            meta = json.load(f)
        cited = set(meta.get("cited_trial_ids", []))
        # Only check if trial fixtures exist; if empty (still Task 13 USER ACTION),
        # this naturally passes vacuously
        if trial_ids:
            missing_trials = cited - trial_ids
            assert not missing_trials, (
                f"{ma_dir.name}: cites trials not in fixtures: {missing_trials}"
            )
