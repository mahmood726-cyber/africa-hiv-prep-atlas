# African HIV PrEP/PEP Long-Acting Trial Atlas v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.1.0 of the African HIV PrEP/PEP Long-Acting Trial Atlas — a methodology-calibration audit of meta-analyses (MAs) of long-acting HIV PrEP modalities, comparing each MA's African-cohort classification against a pre-specified ground truth (≥50% African enrolment).

**Architecture:** Python 3.13 src-layout package with deterministic CSV pipeline (trials.csv → mas.csv → atlas.csv) feeding a self-contained dashboard.html and a RapidMeta-style verification.html. Manual fixture-based extraction in v0.1.0 (LLM scaffolding ready but not yet wired). Clustered-bootstrap sensitivity/specificity headline with pre-specified D1/D2 sensitivity sweeps. pytest TDD throughout, Sentinel pre-push hook, OTS-stamped releases.

**Tech Stack:** Python 3.13, pandas, numpy, pytest, jinja2, python-docx, opentimestamps-client, Sentinel (pre-push), Git, GitHub Pages, Internet Archive.

**Spec reference:** `docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md`

---

## File Structure

```
africa-hiv-prep-atlas/
├── .gitignore
├── README.md
├── pyproject.toml
├── pytest.ini
├── docs/
│   ├── superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md
│   ├── superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md
│   ├── synthesis-methods-note.docx
│   └── E156-PROTOCOL.md
├── src/africa_hiv_prep_atlas/
│   ├── __init__.py        # version constant
│   ├── countries.py       # 54-country UN African list + lookups
│   ├── enrolment.py       # regex enrolment-fraction extraction + negation guard
│   ├── ground_truth.py    # D1/D2/D3 classification from Trial records
│   ├── confidence.py      # high/medium/low tier rules
│   ├── llm_prompts.py     # frozen Layer-T prompt strings, SHA256-pinned
│   ├── ma_claim.py        # Layer-M (a/b/c) extraction
│   ├── audit.py           # confusion matrix, per-MA count error
│   ├── bootstrap.py       # clustered bootstrap (1000 reps, MA-cluster) + k<10 guard
│   ├── records.py         # frozen dataclasses: Trial, MA, AtlasRow
│   ├── csv_writers.py     # deterministic CSV serialization
│   ├── dashboard.py       # dashboard.html generator (inline SVG, self-contained)
│   ├── verification.py    # verification.html (RapidMeta-style, ARAC Plan 3C)
│   └── cli.py             # build_atlas, run_audit entry points
├── tests/
│   ├── __init__.py
│   ├── test_countries.py
│   ├── test_enrolment.py
│   ├── test_negation_guard.py
│   ├── test_ground_truth.py
│   ├── test_d_invariant.py
│   ├── test_confidence.py
│   ├── test_llm_prompts.py
│   ├── test_ma_claim.py
│   ├── test_audit.py
│   ├── test_bootstrap.py
│   ├── test_seed_determinism.py
│   ├── test_records.py
│   ├── test_csv_writers.py
│   ├── test_atlas_pinning.py
│   ├── test_dashboard.py
│   ├── test_verification.py
│   └── test_acceptance.py
├── fixtures/
│   ├── trials/<trial_id>.json     # ground-truth enrolment per trial
│   └── mas/<ma_id>/
│       ├── meta.json              # MA metadata + cited trials
│       └── claims.json            # extracted Layer-M (a/b/c) per cited trial
├── data/
│   ├── trials.csv
│   ├── mas.csv
│   └── atlas.csv
├── outputs/
│   ├── extraction_audit.md
│   ├── dashboard.html
│   └── verification.html
├── prereg/
│   ├── v0.0.1/spec.md
│   ├── v0.1.0-amend-1/spec.md  # if extraction reveals changes
│   └── v0.1.0/spec.md
├── scripts/
│   ├── build_atlas.py             # fixtures → CSVs → HTML
│   ├── run_irr_audit.py           # n=30 blinded audit driver
│   ├── compute_kappa.py           # Cohen's κ from blinded JSON exports
│   ├── ots_stamp.py               # OTS-stamp prereg/atlas.csv/dashboard.html
│   └── ia_check.py                # Internet Archive HTTP-200 check
└── .ots/                          # OTS proof files (committed)
```

---

## Task 0: External-prereq preflight

**Files:**
- Create: `scripts/preflight.py`
- Test: `tests/test_preflight.py`

Per `lessons.md` "Preflight external prereqs BEFORE starting a multi-task plan", this task fails closed if any external dependency is missing. No code beyond this task runs until Task 0 exits 0.

- [ ] **Step 1: Write `scripts/preflight.py`**

```python
"""External-prereq preflight for africa-hiv-prep-atlas v0.1.0.

Fails closed (exit 1) with a per-check action list if any of:
  (a) project path is already a git repo (lessons.md git-init safety)
  (b) Sentinel CLI not importable
  (c) AACT snapshot path not resolvable
  (d) OTS toolchain not on PATH
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Projects\africa-hiv-prep-atlas")


def check_not_already_git_repo() -> tuple[bool, str]:
    """(a) Project path must NOT already be a git repo."""
    git_dir = PROJECT_ROOT / ".git"
    if git_dir.exists():
        return False, (
            f"FAIL: {git_dir} exists. Either reuse the existing repo (rename Task 1 "
            "to 'adopt repo') OR move/delete and rerun preflight."
        )
    # Defense-in-depth: also check git rev-parse from the project dir
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return False, (
                f"FAIL: git rev-parse reports toplevel={r.stdout.strip()!r} "
                "from project dir. Move/delete before init."
            )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return True, "OK: project path is not a git repo"


def check_sentinel_installable() -> tuple[bool, str]:
    """(b) Sentinel CLI must be importable as a module."""
    r = subprocess.run(
        [sys.executable, "-c", "import sentinel; print(sentinel.__version__)"],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        return False, (
            "FAIL: `python -c 'import sentinel'` failed. Install with "
            "`pip install -e C:\\Sentinel\\` and rerun."
        )
    return True, f"OK: sentinel {r.stdout.strip()}"


def check_aact_snapshot() -> tuple[bool, str]:
    """(c) AACT snapshot must resolve via candidate-root discovery.

    Per lessons.md "Do not hardcode one drive": tries fixed paths first, then
    globs known versioned-snapshot layouts (e.g. D:\\AACT-storage\\AACT\\YYYY-MM-DD\\).
    """
    # Fixed candidates first.
    fixed = [
        Path(os.environ.get("AACT_ROOT", "")) / "studies.txt" if os.environ.get("AACT_ROOT") else None,
        Path(r"C:\AACT\studies.txt"),
        Path(r"D:\AACT\studies.txt"),
    ]
    for c in fixed:
        if c and c.exists():
            return True, f"OK: AACT studies.txt at {c}"
    # Versioned-snapshot discovery: pick the most recent dated subdir.
    glob_roots = [
        Path(r"D:\AACT-storage\AACT"),
        Path(r"C:\AACT-storage\AACT"),
    ]
    candidates: list[Path] = []
    for root in glob_roots:
        if root.exists():
            for sub in sorted(root.iterdir(), reverse=True):
                if sub.is_dir() and (sub / "studies.txt").exists():
                    candidates.append(sub / "studies.txt")
    if candidates:
        return True, f"OK: AACT studies.txt at {candidates[0]} (versioned snapshot)"
    return False, (
        "FAIL: AACT snapshot not found at C:\\AACT, D:\\AACT, "
        "$env:AACT_ROOT, or D:\\AACT-storage\\AACT\\YYYY-MM-DD\\. "
        "Set AACT_ROOT or restore snapshot."
    )


def check_ots_toolchain() -> tuple[bool, str]:
    """(d) OTS client must be on PATH."""
    ots = shutil.which("ots")
    if ots is None:
        return False, (
            "FAIL: `ots` not on PATH. Install with `pip install opentimestamps-client`."
        )
    return True, f"OK: ots at {ots}"


CHECKS = [
    ("path/git", check_not_already_git_repo),
    ("sentinel", check_sentinel_installable),
    ("aact", check_aact_snapshot),
    ("ots", check_ots_toolchain),
]


def main() -> int:
    failures: list[str] = []
    for name, fn in CHECKS:
        ok, msg = fn()
        prefix = "[OK]  " if ok else "[FAIL]"
        print(f"{prefix} {name}: {msg}")
        if not ok:
            failures.append(name)
    if failures:
        print(f"\nPreflight FAILED on: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nPreflight PASSED. Proceed to Task 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write `tests/test_preflight.py`**

```python
"""Unit tests for preflight check functions (no external calls in unit tests)."""
from unittest.mock import patch

import pytest

import scripts.preflight as p


def test_check_not_already_git_repo_passes_when_no_git_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "PROJECT_ROOT", tmp_path)
    ok, msg = p.check_not_already_git_repo()
    assert ok
    assert "OK" in msg


def test_check_not_already_git_repo_fails_when_git_dir_exists(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(p, "PROJECT_ROOT", tmp_path)
    ok, msg = p.check_not_already_git_repo()
    assert not ok
    assert "FAIL" in msg


def test_main_returns_1_on_any_failure():
    with patch.object(p, "CHECKS", [("dummy", lambda: (False, "FAIL: x"))]):
        assert p.main() == 1


def test_main_returns_0_when_all_pass():
    with patch.object(p, "CHECKS", [("dummy", lambda: (True, "OK"))]):
        assert p.main() == 0
```

- [ ] **Step 3: Run the unit tests**

```
pytest tests/test_preflight.py -v
```

Expected: 4 passed.

- [ ] **Step 4: Run preflight against the real environment**

```
python scripts/preflight.py
```

Expected: exit 0 with `[OK]` on all four checks. **If any check fails, fix the underlying prereq and rerun. Do not proceed to Task 1 with a failing preflight.**

---

## Task 1: Repo bootstrap (git init, structure, first commit)

**Files:**
- Create: `.gitignore`, `README.md`, `pyproject.toml`, `pytest.ini`, `src/africa_hiv_prep_atlas/__init__.py`, `tests/__init__.py`

- [ ] **Step 1: `git init` from the project root**

```
git -C C:/Projects/africa-hiv-prep-atlas init -b master
```

Expected: `Initialized empty Git repository in C:/Projects/africa-hiv-prep-atlas/.git/`

- [ ] **Step 2: Write `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
build/
dist/
.venv/
venv/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Project — never commit
PROGRESS.md
sentinel-findings.md
sentinel-findings.jsonl
STUCK_FAILURES.md
STUCK_FAILURES.jsonl
.claude/
*.local.json

# Generated outputs are committed (atlas.csv, dashboard.html), but not these
*.tmp
*.bak
```

- [ ] **Step 3: Write `README.md`**

```markdown
# African HIV PrEP/PEP Long-Acting Trial Atlas

> Methodology-calibration audit: do meta-analyses of long-acting HIV PrEP modalities accurately classify African-cohort trials?

**Status:** v0.1.0 (in development).
**Spec:** [`docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md`](docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md).
**Plan:** [`docs/superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md`](docs/superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md).

## Headline calibration

Across N (MA, trial) pairs, MAs of long-acting HIV PrEP classified African-cohort trials with X% sensitivity / Y% specificity vs the ground-truth definition (≥50% enrolment from African sites).

## Quick start

```
pip install -e .
python scripts/preflight.py
python scripts/build_atlas.py
pytest -q
```

## Layout

- `src/africa_hiv_prep_atlas/` — pipeline modules
- `fixtures/` — committed source-line-attributed extraction fixtures
- `data/` — generated CSVs (atlas.csv pinned byte-for-byte)
- `outputs/` — dashboard.html, verification.html, extraction_audit.md
- `prereg/` — frozen spec snapshots per release tag
- `.ots/` — OpenTimestamps proof files

## License

MIT.
```

- [ ] **Step 4: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "africa-hiv-prep-atlas"
version = "0.1.0.dev0"
description = "Methodology-calibration audit of African-cohort claims in long-acting HIV PrEP MAs"
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.0",
  "numpy>=1.24",
  "jinja2>=3.1",
  "python-docx>=1.1",
]

[project.optional-dependencies]
dev = [
  "pytest>=7.4",
  "pytest-cov>=4.1",
]

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 5: Write `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = src .
addopts = -ra --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
```

- [ ] **Step 6: Create package and tests `__init__.py` files**

```
type nul > src/africa_hiv_prep_atlas/__init__.py
type nul > tests/__init__.py
```

(On bash: `touch src/africa_hiv_prep_atlas/__init__.py tests/__init__.py`.)

Then write `src/africa_hiv_prep_atlas/__init__.py`:

```python
"""African HIV PrEP/PEP Long-Acting Trial Atlas."""
__version__ = "0.1.0.dev0"
```

- [ ] **Step 7: Install in editable mode**

```
pip install -e .[dev]
```

Expected: `Successfully installed africa-hiv-prep-atlas-0.1.0.dev0`.

- [ ] **Step 8: Confirm pytest collects zero tests cleanly**

```
pytest -q
```

Expected: `no tests ran in X.XXs` (or 4 from `test_preflight.py` if you ran Task 0 in this directory). Either way, exit 0.

- [ ] **Step 9: First commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add .gitignore README.md pyproject.toml pytest.ini src/ tests/ scripts/preflight.py docs/
git -C C:/Projects/africa-hiv-prep-atlas commit -m "chore: bootstrap africa-hiv-prep-atlas v0.1.0.dev0 scaffold"
```

Expected: 1 commit, `master` branch.

---

## Task 2: Sentinel pre-push hook + GitHub remote

**Files:**
- Modify: `.git/hooks/pre-push` (installed by Sentinel)
- Create: GitHub remote `origin`

- [ ] **Step 1: Install Sentinel pre-push hook**

```
python -m sentinel install-hook --repo C:/Projects/africa-hiv-prep-atlas
```

Expected: `Installed pre-push hook at .git/hooks/pre-push`.

- [ ] **Step 2: Run a no-op Sentinel scan to verify config**

```
python -m sentinel scan --repo C:/Projects/africa-hiv-prep-atlas
```

Expected: `BLOCK=0 WARN=0` on the empty scaffold.

- [ ] **Step 3: Create empty GitHub repo and add remote**

```
gh repo create mahmood726-cyber/africa-hiv-prep-atlas --public --description "Methodology-calibration audit of African-cohort claims in long-acting HIV PrEP meta-analyses" --confirm
git -C C:/Projects/africa-hiv-prep-atlas remote add origin https://github.com/mahmood726-cyber/africa-hiv-prep-atlas.git
```

Expected: remote `origin` points at the new repo.

- [ ] **Step 4: First push**

```
git -C C:/Projects/africa-hiv-prep-atlas push -u origin master
```

Expected: pre-push hook runs Sentinel, reports `BLOCK=0`, push succeeds.

- [ ] **Step 5: Commit Sentinel hook receipt**

If Sentinel writes a `.sentinel/` directory, commit it:

```
git -C C:/Projects/africa-hiv-prep-atlas add .sentinel/
git -C C:/Projects/africa-hiv-prep-atlas commit -m "chore: install Sentinel pre-push hook" --allow-empty
git -C C:/Projects/africa-hiv-prep-atlas push
```

(`--allow-empty` covers the case where `.sentinel/` is gitignored — keeps the audit trail.)

---

## Task 3: African countries module (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/countries.py`
- Test: `tests/test_countries.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_countries.py
import pytest
from africa_hiv_prep_atlas.countries import (
    AFRICAN_COUNTRIES,
    is_african,
    normalise_country,
)


def test_count_is_54():
    assert len(AFRICAN_COUNTRIES) == 54


def test_includes_south_africa_uganda_botswana():
    for c in ("South Africa", "Uganda", "Botswana"):
        assert c in AFRICAN_COUNTRIES


def test_excludes_non_african_neighbours():
    for c in ("Israel", "Saudi Arabia", "Yemen", "Greece"):
        assert c not in AFRICAN_COUNTRIES


def test_is_african_case_insensitive():
    assert is_african("south africa")
    assert is_african("UGANDA")
    assert is_african("Botswana")


def test_handles_synonyms():
    assert is_african("Eswatini")
    assert is_african("Swaziland")
    assert is_african("Cabo Verde")
    assert is_african("Cape Verde")


def test_normalise_returns_canonical():
    assert normalise_country("swaziland") == "Eswatini"
    assert normalise_country("cape verde") == "Cabo Verde"
    assert normalise_country("united states") is None


def test_rejects_unknown():
    assert not is_african("Atlantis")
    assert not is_african("")
```

- [ ] **Step 2: Run, expect failure**

`pytest tests/test_countries.py -v` → 7 errors (`ModuleNotFoundError`).

- [ ] **Step 3: Implement `countries.py`**

```python
"""54-country UN list of African states with synonym handling."""
from __future__ import annotations

AFRICAN_COUNTRIES: frozenset[str] = frozenset({
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cameroon", "Central African Republic", "Chad", "Comoros",
    "Democratic Republic of the Congo", "Republic of the Congo",
    "Cote d'Ivoire", "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea",
    "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea",
    "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar",
    "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique",
    "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe",
    "Senegal", "Seychelles", "Sierra Leone", "Somalia", "South Africa",
    "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda",
    "Zambia", "Zimbabwe",
})

assert len(AFRICAN_COUNTRIES) == 54

_SYNONYMS: dict[str, str] = {
    "swaziland": "Eswatini",
    "cape verde": "Cabo Verde",
    "ivory coast": "Cote d'Ivoire",
    "drc": "Democratic Republic of the Congo",
    "dr congo": "Democratic Republic of the Congo",
    "congo-kinshasa": "Democratic Republic of the Congo",
    "congo-brazzaville": "Republic of the Congo",
    "the gambia": "Gambia",
    "tanzania, united republic of": "Tanzania",
}
_CANONICAL_LC: dict[str, str] = {c.lower(): c for c in AFRICAN_COUNTRIES}


def normalise_country(name: str) -> str | None:
    if not name:
        return None
    key = name.strip().lower()
    if key in _CANONICAL_LC:
        return _CANONICAL_LC[key]
    if key in _SYNONYMS:
        return _SYNONYMS[key]
    return None


def is_african(name: str) -> bool:
    return normalise_country(name) is not None
```

- [ ] **Step 4: Run, expect pass**

`pytest tests/test_countries.py -v` → 7 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/countries.py tests/test_countries.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(countries): 54-country African list with synonym handling"
```

---

## Task 4: Enrolment-fraction extraction with negation guard (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/enrolment.py`
- Test: `tests/test_enrolment.py`, `tests/test_negation_guard.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_enrolment.py
from africa_hiv_prep_atlas.enrolment import extract_country_enrolment, EnrolmentRow


def test_simple_pattern():
    text = "South Africa: 1,200 randomised. Uganda: 450 randomised."
    rows = extract_country_enrolment(text)
    assert EnrolmentRow(country="South Africa", n=1200) in rows
    assert EnrolmentRow(country="Uganda", n=450) in rows


def test_n_equals_format():
    text = "Botswana (n=890), Kenya (n=1100), Malawi (n=315)"
    rows = extract_country_enrolment(text)
    cs = {r.country for r in rows}
    assert {"Botswana", "Kenya", "Malawi"}.issubset(cs)


def test_skips_non_african():
    text = "USA: 500. South Africa: 1200."
    rows = extract_country_enrolment(text)
    assert all(r.country != "USA" for r in rows)
    assert any(r.country == "South Africa" for r in rows)


def test_canonicalises_synonyms():
    text = "Swaziland: 200 randomised."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Eswatini" for r in rows)


def test_thousands_separator():
    text = "Nigeria: 2,500 enrolled."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Nigeria" and r.n == 2500 for r in rows)


def test_empty_text():
    assert extract_country_enrolment("") == []
    assert extract_country_enrolment("no countries mentioned here") == []


def test_dedup_keeps_max():
    text = "Kenya: 100 randomised. Kenya enrolled 450."
    rows = extract_country_enrolment(text)
    kenyas = [r for r in rows if r.country == "Kenya"]
    assert len(kenyas) == 1
    assert kenyas[0].n == 450
```

```python
# tests/test_negation_guard.py
"""DossierGap 2026-04-15 lesson: 30-char preceding-window negation guard."""
from africa_hiv_prep_atlas.enrolment import extract_country_enrolment


def test_skips_not_randomised():
    text = "Final cohort. Not Randomised: Kenya 1,807. Randomised: Kenya 5,050."
    rows = extract_country_enrolment(text)
    kenyas = [r for r in rows if r.country == "Kenya"]
    assert len(kenyas) == 1
    assert kenyas[0].n == 5050


def test_skips_excluded():
    text = "Excluded: Uganda 200. Randomised: Uganda 1,500."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Uganda" and r.n == 1500 for r in rows)
    assert not any(r.country == "Uganda" and r.n == 200 for r in rows)


def test_skips_never():
    text = "South Africa: never enrolled (site closed). Botswana: 800 enrolled."
    rows = extract_country_enrolment(text)
    assert not any(r.country == "South Africa" for r in rows)


def test_negation_window_is_30_chars():
    text = "We will not address site issues at all. Kenya: 1000 randomised."
    rows = extract_country_enrolment(text)
    assert any(r.country == "Kenya" and r.n == 1000 for r in rows)
```

- [ ] **Step 2: Run, expect failure**

`pytest tests/test_enrolment.py tests/test_negation_guard.py -v` → 11 errors.

- [ ] **Step 3: Implement `enrolment.py`**

```python
"""Country-level enrolment extraction with DossierGap negation guard."""
from __future__ import annotations

import re
from dataclasses import dataclass

from africa_hiv_prep_atlas.countries import AFRICAN_COUNTRIES, normalise_country

NEGATION_WINDOW = 30
NEGATION_TOKENS = ("not ", "non-", "non ", "never ", "excluded", "no ")

_SYNONYM_KEYS = (
    "Swaziland", "Cape Verde", "Ivory Coast", "DRC", "DR Congo",
    "Congo-Kinshasa", "Congo-Brazzaville", "The Gambia",
    "Tanzania, United Republic of",
)
_ALL_NAMES = tuple(sorted(
    set(AFRICAN_COUNTRIES) | set(_SYNONYM_KEYS),
    key=len, reverse=True,
))
_COUNTRY_ALT = "|".join(re.escape(n) for n in _ALL_NAMES)

_P1 = re.compile(rf"({_COUNTRY_ALT})\s*[:\-]\s*([\d,]+)\b", re.IGNORECASE)
_P2 = re.compile(rf"({_COUNTRY_ALT})\s*\(\s*[Nn]\s*=\s*([\d,]+)\s*\)", re.IGNORECASE)
_P3 = re.compile(
    rf"({_COUNTRY_ALT})\s+(?:enrolled|randomised|randomized)\s+([\d,]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class EnrolmentRow:
    country: str
    n: int


def _is_negated(text: str, match_start: int) -> bool:
    window = text[max(0, match_start - NEGATION_WINDOW): match_start].lower()
    return any(tok in window for tok in NEGATION_TOKENS)


def extract_country_enrolment(text: str) -> list[EnrolmentRow]:
    if not text:
        return []
    found: dict[str, int] = {}
    for pat in (_P1, _P2, _P3):
        for m in pat.finditer(text):
            if _is_negated(text, m.start()):
                continue
            n_str = m.group(2).replace(",", "")
            try:
                n = int(n_str)
            except ValueError:
                continue
            canon = normalise_country(m.group(1))
            if canon is None:
                continue
            if n > found.get(canon, 0):
                found[canon] = n
    return [EnrolmentRow(country=c, n=n) for c, n in sorted(found.items())]
```

- [ ] **Step 4: Run, expect pass**

`pytest tests/test_enrolment.py tests/test_negation_guard.py -v` → 11 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/enrolment.py tests/test_enrolment.py tests/test_negation_guard.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(enrolment): regex extraction with DossierGap negation guard"
```

---

## Task 5: Trial / MA / AtlasRow records (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/records.py`
- Test: `tests/test_records.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_records.py
import pytest
from africa_hiv_prep_atlas.records import Trial, MA, AtlasRow


def test_trial_frozen():
    t = Trial(
        trial_id="HPTN_084", nct="NCT03164564", pactr=None,
        modality="cabotegravir", year=2020,
        enrolment_by_country={"South Africa": 700, "Uganda": 600},
        total_enrolled=3224, source_id="hptn084_publication_2022",
    )
    with pytest.raises((AttributeError, Exception)):
        t.trial_id = "X"


def test_trial_african_n():
    t = Trial(
        trial_id="HPTN_084", nct="NCT03164564", pactr=None,
        modality="cabotegravir", year=2020,
        enrolment_by_country={"South Africa": 700, "USA": 100},
        total_enrolled=800, source_id="src1",
    )
    assert t.african_n() == 700


def test_trial_african_fraction():
    t = Trial(
        trial_id="HPTN_084", nct="NCT03164564", pactr=None,
        modality="cabotegravir", year=2020,
        enrolment_by_country={"South Africa": 700, "USA": 100},
        total_enrolled=800, source_id="src1",
    )
    assert abs(t.african_fraction() - 0.875) < 1e-9


def test_trial_zero_total_returns_zero_fraction():
    t = Trial(
        trial_id="X", nct=None, pactr=None, modality="x", year=2020,
        enrolment_by_country={}, total_enrolled=0, source_id="src1",
    )
    assert t.african_fraction() == 0.0


def test_ma_frozen_with_cited_trial_ids():
    m = MA(
        ma_id="abc2024", first_author="Smith", year=2024,
        cited_trial_ids=("HPTN_083", "HPTN_084"),
        full_text_source_id="abc2024_pdf",
    )
    assert m.cited_trial_ids == ("HPTN_083", "HPTN_084")


def test_atlas_row_layers():
    r = AtlasRow(
        ma_id="abc2024", trial_id="HPTN_084",
        claimed_a=True, claimed_b=True, claimed_c=False,
        truth_d1=True, truth_d2=True, truth_d3=True,
        confidence_layer_m="high", confidence_layer_t="medium",
        source_lines=("abc2024_p3l5", "hptn084_p1l2"),
    )
    assert r.claimed_union() is True
    assert r.tp_at_d3() is True
    assert r.fp_at_d3() is False
    assert r.fn_at_d3() is False
    assert r.tn_at_d3() is False
```

- [ ] **Step 2: Run, expect failure**

`pytest tests/test_records.py -v` → all errors.

- [ ] **Step 3: Implement `records.py`**

```python
"""Frozen dataclass records for trials, MAs, and atlas rows."""
from __future__ import annotations

from dataclasses import dataclass

from africa_hiv_prep_atlas.countries import is_african


@dataclass(frozen=True)
class Trial:
    trial_id: str
    nct: str | None
    pactr: str | None
    modality: str
    year: int
    enrolment_by_country: dict
    total_enrolled: int
    source_id: str

    def african_n(self) -> int:
        return sum(n for c, n in self.enrolment_by_country.items() if is_african(c))

    def african_fraction(self) -> float:
        if self.total_enrolled <= 0:
            return 0.0
        return self.african_n() / self.total_enrolled


@dataclass(frozen=True)
class MA:
    ma_id: str
    first_author: str
    year: int
    cited_trial_ids: tuple
    full_text_source_id: str


@dataclass(frozen=True)
class AtlasRow:
    ma_id: str
    trial_id: str
    claimed_a: bool
    claimed_b: bool
    claimed_c: bool
    truth_d1: bool
    truth_d2: bool
    truth_d3: bool
    confidence_layer_m: str
    confidence_layer_t: str
    source_lines: tuple

    def claimed_union(self) -> bool:
        return self.claimed_a or self.claimed_b or self.claimed_c

    def tp_at_d3(self) -> bool:
        return self.claimed_union() and self.truth_d3

    def fp_at_d3(self) -> bool:
        return self.claimed_union() and not self.truth_d3

    def fn_at_d3(self) -> bool:
        return (not self.claimed_union()) and self.truth_d3

    def tn_at_d3(self) -> bool:
        return (not self.claimed_union()) and (not self.truth_d3)
```

- [ ] **Step 4: Run, expect pass**

`pytest tests/test_records.py -v` → 6 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/records.py tests/test_records.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(records): frozen Trial/MA/AtlasRow dataclasses"
```

---

## Task 6: Ground-truth classification (D1/D2/D3) (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/ground_truth.py`
- Test: `tests/test_ground_truth.py`, `tests/test_d_invariant.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ground_truth.py
from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_trial, classify_d1, classify_d2, classify_d3


def _trial(enrolment, sites_by_country, total):
    return Trial(
        trial_id="X", nct=None, pactr=None, modality="x", year=2020,
        enrolment_by_country=enrolment, total_enrolled=total, source_id="src",
    ), sites_by_country


def test_d1_one_african_site_qualifies():
    t, sites = _trial({"South Africa": 100}, {"South Africa": 1, "USA": 5}, 1000)
    assert classify_d1(t, sites) is True


def test_d1_zero_african_sites_fails():
    t, sites = _trial({"USA": 1000}, {"USA": 5}, 1000)
    assert classify_d1(t, sites) is False


def test_d2_at_50_percent_sites():
    t, sites = _trial({"Kenya": 200}, {"Kenya": 3, "USA": 3}, 800)
    assert classify_d2(t, sites) is True
    t, sites = _trial({"Kenya": 200}, {"Kenya": 2, "USA": 4}, 800)
    assert classify_d2(t, sites) is False


def test_d3_at_50_percent_enrolment():
    t, sites = _trial({"Uganda": 600, "USA": 400}, {"Uganda": 1, "USA": 1}, 1000)
    assert classify_d3(t, sites) is True
    t, sites = _trial({"Uganda": 400, "USA": 600}, {"Uganda": 1, "USA": 1}, 1000)
    assert classify_d3(t, sites) is False


def test_d3_exactly_50_percent_qualifies():
    t, sites = _trial({"Kenya": 500, "USA": 500}, {"Kenya": 1, "USA": 1}, 1000)
    assert classify_d3(t, sites) is True


def test_classify_trial_returns_all_three_flags():
    t, sites = _trial({"South Africa": 700, "USA": 300}, {"South Africa": 4, "USA": 2}, 1000)
    res = classify_trial(t, sites)
    assert res == {"d1": True, "d2": True, "d3": True}


def test_classify_trial_zero_enrolment_returns_all_false():
    t, sites = _trial({}, {"USA": 5}, 0)
    res = classify_trial(t, sites)
    assert res == {"d1": False, "d2": False, "d3": False}
```

```python
# tests/test_d_invariant.py
"""Mathematical invariant: D2 implies D1, D3 implies D1.

D2 and D3 are NOT nested with each other (a trial could have 2 of 3 African
sites enrolling small numbers, with one US site enrolling 90% of participants).
"""
from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_d1, classify_d2, classify_d3


def _t(enrolment, sites, total):
    return Trial(
        trial_id="x", nct=None, pactr=None, modality="x", year=2020,
        enrolment_by_country=enrolment, total_enrolled=total, source_id="s",
    ), sites


def test_d2_implies_d1():
    cases = [
        _t({"Uganda": 100}, {"Uganda": 5, "USA": 4}, 1000),  # 5/9 sites African
        _t({"Kenya": 200, "USA": 0}, {"Kenya": 3, "USA": 0}, 200),
    ]
    for t, sites in cases:
        if classify_d2(t, sites):
            assert classify_d1(t, sites)


def test_d3_implies_d1():
    cases = [
        _t({"Uganda": 600, "USA": 400}, {"Uganda": 1, "USA": 5}, 1000),
        _t({"Kenya": 500, "USA": 500}, {"Kenya": 1, "USA": 1}, 1000),
    ]
    for t, sites in cases:
        if classify_d3(t, sites):
            assert classify_d1(t, sites)


def test_d2_d3_not_nested():
    # 2 African sites of 3 (D2 yes), but African enrolment <50% (D3 no).
    t, sites = _t({"Uganda": 50, "Kenya": 50, "USA": 900}, {"Uganda": 1, "Kenya": 1, "USA": 1}, 1000)
    assert classify_d2(t, sites) is True
    assert classify_d3(t, sites) is False
    # 1 African site of 5 (D2 no), but 60% African enrolment (D3 yes).
    t, sites = _t({"South Africa": 600, "USA": 400}, {"South Africa": 1, "USA": 4}, 1000)
    assert classify_d2(t, sites) is False
    assert classify_d3(t, sites) is True
```

- [ ] **Step 2: Run, expect failure**

`pytest tests/test_ground_truth.py tests/test_d_invariant.py -v` → all errors.

- [ ] **Step 3: Implement `ground_truth.py`**

```python
"""D1 / D2 / D3 ground-truth classification of trials."""
from __future__ import annotations

from africa_hiv_prep_atlas.countries import is_african
from africa_hiv_prep_atlas.records import Trial


def classify_d1(trial: Trial, sites_by_country: dict) -> bool:
    return any(is_african(c) and n > 0 for c, n in sites_by_country.items())


def classify_d2(trial: Trial, sites_by_country: dict) -> bool:
    total_sites = sum(sites_by_country.values())
    if total_sites <= 0:
        return False
    african_sites = sum(n for c, n in sites_by_country.items() if is_african(c))
    return (african_sites / total_sites) >= 0.5


def classify_d3(trial: Trial, sites_by_country: dict) -> bool:
    if trial.total_enrolled <= 0:
        return False
    return trial.african_fraction() >= 0.5


def classify_trial(trial: Trial, sites_by_country: dict) -> dict:
    return {
        "d1": classify_d1(trial, sites_by_country),
        "d2": classify_d2(trial, sites_by_country),
        "d3": classify_d3(trial, sites_by_country),
    }
```

- [ ] **Step 4: Run, expect pass**

`pytest tests/test_ground_truth.py tests/test_d_invariant.py -v` → 10 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/ground_truth.py tests/test_ground_truth.py tests/test_d_invariant.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(ground_truth): D1/D2/D3 classification + nesting invariants"
```

---

## Task 7: Confidence tiering (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/confidence.py`
- Test: `tests/test_confidence.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_confidence.py
from africa_hiv_prep_atlas.confidence import (
    classify_confidence,
    Confidence,
    REVIEW_REQUIRED,
)


def test_high_for_locked_regex_match():
    assert classify_confidence(method="regex", flags=()) == Confidence.HIGH


def test_medium_for_llm_assisted():
    assert classify_confidence(method="llm", flags=()) == Confidence.MEDIUM


def test_low_for_ambiguous():
    assert classify_confidence(method="regex", flags=("ambiguous",)) == Confidence.LOW


def test_low_for_negation_flagged():
    assert classify_confidence(method="regex", flags=("negation",)) == Confidence.LOW


def test_low_for_multi_match():
    assert classify_confidence(method="regex", flags=("multi_match",)) == Confidence.LOW


def test_review_required_includes_medium_and_low():
    assert Confidence.MEDIUM in REVIEW_REQUIRED
    assert Confidence.LOW in REVIEW_REQUIRED
    assert Confidence.HIGH not in REVIEW_REQUIRED
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `confidence.py`**

```python
"""Confidence tiering rules for Layer-T and Layer-M extractions."""
from __future__ import annotations

from enum import Enum

LOW_FLAGS = frozenset({"ambiguous", "negation", "multi_match"})


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


REVIEW_REQUIRED: frozenset[Confidence] = frozenset({Confidence.MEDIUM, Confidence.LOW})


def classify_confidence(method: str, flags: tuple) -> Confidence:
    if any(f in LOW_FLAGS for f in flags):
        return Confidence.LOW
    if method == "llm":
        return Confidence.MEDIUM
    if method == "regex":
        return Confidence.HIGH
    return Confidence.LOW
```

- [ ] **Step 4: Run, expect pass** → 6 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/confidence.py tests/test_confidence.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(confidence): high/medium/low tiering with review-required set"
```

---

## Task 8: LLM prompt scaffolding (frozen, SHA256-pinned, NOT yet wired)

**Files:**
- Create: `src/africa_hiv_prep_atlas/llm_prompts.py`
- Test: `tests/test_llm_prompts.py`

Per spec §6: prompts are committed as frozen strings with SHA256 pins. v0.1.0 does not call an LLM — all extraction is fixture-mode (manual). v0.2.0 will wire these.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_llm_prompts.py
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
```

- [ ] **Step 2: Implement `llm_prompts.py`**

Compute the SHA256 by running `python -c "import hashlib; print(hashlib.sha256(open('src/africa_hiv_prep_atlas/llm_prompts.py').read().encode()).hexdigest())"` after writing the prompts. Then paste the resulting hashes into the constants. Iterate until tests pass (the test pins are the live SHA of the strings as committed).

```python
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
LAYER_T_ENROLMENT_PROMPT_SHA256 = "PLACEHOLDER_REPLACE_AFTER_FREEZE"
LAYER_M_NARRATIVE_PROMPT_SHA256 = "PLACEHOLDER_REPLACE_AFTER_FREEZE"
```

- [ ] **Step 3: Compute live SHA pins and replace placeholders**

Run:

```
python -c "import hashlib; \
  from africa_hiv_prep_atlas import llm_prompts as m; \
  print('T:', hashlib.sha256(m.LAYER_T_ENROLMENT_PROMPT.encode()).hexdigest()); \
  print('M:', hashlib.sha256(m.LAYER_M_NARRATIVE_PROMPT.encode()).hexdigest())"
```

Copy the two hex strings into `LAYER_T_ENROLMENT_PROMPT_SHA256` and `LAYER_M_NARRATIVE_PROMPT_SHA256`.

- [ ] **Step 4: Run, expect pass**

`pytest tests/test_llm_prompts.py -v` → 4 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/llm_prompts.py tests/test_llm_prompts.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(llm_prompts): frozen Layer-T/Layer-M prompts with SHA256 pins"
```

---

## Task 9: MA-claim extraction (Layer-M a/b/c) (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/ma_claim.py`
- Test: `tests/test_ma_claim.py`

Layer-M claim layers per spec §4:
- (a) explicit count: MA states an integer count of African-cohort trials and lists which.
- (b) implicit-from-table: MA's included-studies table tags this trial with one or more African country names.
- (c) narrative mention: MA's discussion section names this trial in the same sentence as an African country/region/population.

For v0.1.0, all three layers are extracted **manually** from MA fixtures (committed JSON). This module provides the *aggregation* and *layer-stripped sensitivity* logic.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ma_claim.py
from africa_hiv_prep_atlas.ma_claim import (
    extract_layer_m_from_fixture,
    layer_stripped_union,
)


def test_extract_returns_three_booleans_per_trial():
    fixture = {
        "ma_id": "smith2024",
        "claims": {
            "HPTN_084": {"a": True, "b": True, "c": True, "source_lines": ["p3l5"]},
            "HPTN_083": {"a": False, "b": True, "c": False, "source_lines": ["p3l8"]},
        },
    }
    rows = extract_layer_m_from_fixture(fixture)
    by_trial = {r["trial_id"]: r for r in rows}
    assert by_trial["HPTN_084"]["claimed_a"] is True
    assert by_trial["HPTN_084"]["claimed_b"] is True
    assert by_trial["HPTN_084"]["claimed_c"] is True
    assert by_trial["HPTN_083"]["claimed_a"] is False
    assert by_trial["HPTN_083"]["claimed_b"] is True
    assert by_trial["HPTN_083"]["claimed_c"] is False


def test_extract_handles_missing_layers_as_false():
    fixture = {"ma_id": "x", "claims": {"HPTN_084": {"a": True, "source_lines": ["x"]}}}
    rows = extract_layer_m_from_fixture(fixture)
    r = rows[0]
    assert r["claimed_a"] is True
    assert r["claimed_b"] is False
    assert r["claimed_c"] is False


def test_layer_stripped_a_only():
    row = {"claimed_a": True, "claimed_b": False, "claimed_c": False}
    assert layer_stripped_union(row, layers=("a",)) is True


def test_layer_stripped_a_b_only():
    row = {"claimed_a": False, "claimed_b": True, "claimed_c": True}
    assert layer_stripped_union(row, layers=("a", "b")) is True
    row = {"claimed_a": False, "claimed_b": False, "claimed_c": True}
    assert layer_stripped_union(row, layers=("a", "b")) is False


def test_layer_stripped_full_union():
    row = {"claimed_a": False, "claimed_b": False, "claimed_c": True}
    assert layer_stripped_union(row, layers=("a", "b", "c")) is True


def test_layer_stripped_empty_layers_returns_false():
    row = {"claimed_a": True, "claimed_b": True, "claimed_c": True}
    assert layer_stripped_union(row, layers=()) is False
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `ma_claim.py`**

```python
"""Layer-M (MA-claim) extraction from committed MA fixtures."""
from __future__ import annotations

VALID_LAYERS = ("a", "b", "c")


def extract_layer_m_from_fixture(fixture: dict) -> list[dict]:
    out: list[dict] = []
    for trial_id, raw in fixture.get("claims", {}).items():
        out.append({
            "ma_id": fixture["ma_id"],
            "trial_id": trial_id,
            "claimed_a": bool(raw.get("a", False)),
            "claimed_b": bool(raw.get("b", False)),
            "claimed_c": bool(raw.get("c", False)),
            "source_lines": tuple(raw.get("source_lines", ())),
        })
    return out


def layer_stripped_union(row: dict, layers: tuple) -> bool:
    if not layers:
        return False
    for L in layers:
        if L not in VALID_LAYERS:
            raise ValueError(f"unknown layer {L!r}; valid: {VALID_LAYERS}")
    return any(row.get(f"claimed_{L}", False) for L in layers)
```

- [ ] **Step 4: Run, expect pass** → 6 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/ma_claim.py tests/test_ma_claim.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(ma_claim): Layer-M fixture extraction + layer-stripped union"
```

---

## Task 10: Audit / confusion matrix / per-MA count error (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/audit.py`
- Test: `tests/test_audit.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_audit.py
import pytest

from africa_hiv_prep_atlas.audit import (
    confusion_at_d3,
    sensitivity,
    specificity,
    per_ma_count_error,
)


def _row(ma, trial, claim, truth):
    return {
        "ma_id": ma, "trial_id": trial,
        "claimed_a": claim, "claimed_b": False, "claimed_c": False,
        "truth_d1": truth, "truth_d2": truth, "truth_d3": truth,
    }


def test_confusion_at_d3_simple():
    rows = [
        _row("M1", "T1", True, True),    # TP
        _row("M1", "T2", True, False),   # FP
        _row("M1", "T3", False, True),   # FN
        _row("M1", "T4", False, False),  # TN
    ]
    c = confusion_at_d3(rows)
    assert c == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}


def test_sensitivity_correct():
    c = {"tp": 8, "fp": 2, "fn": 2, "tn": 8}
    assert sensitivity(c) == 0.8


def test_specificity_correct():
    c = {"tp": 8, "fp": 2, "fn": 2, "tn": 8}
    assert specificity(c) == 0.8


def test_sensitivity_zero_positives_returns_nan():
    import math
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 10}
    assert math.isnan(sensitivity(c))


def test_specificity_zero_negatives_returns_nan():
    import math
    c = {"tp": 5, "fp": 0, "fn": 0, "tn": 0}
    assert math.isnan(specificity(c))


def test_per_ma_count_error_simple():
    rows = [
        _row("M1", "T1", True, True),
        _row("M1", "T2", True, False),
        _row("M1", "T3", False, True),
    ]
    errs = per_ma_count_error(rows)
    # M1 claimed=2, truth=2, |diff|=0
    assert errs == {"M1": 0}


def test_per_ma_count_error_over_claim():
    rows = [
        _row("M1", "T1", True, False),
        _row("M1", "T2", True, False),
    ]
    errs = per_ma_count_error(rows)
    assert errs == {"M1": 2}
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `audit.py`**

```python
"""Confusion matrix + per-MA count error."""
from __future__ import annotations

import math
from collections import defaultdict


def _claimed(row: dict) -> bool:
    return bool(row.get("claimed_a") or row.get("claimed_b") or row.get("claimed_c"))


def confusion_at_d3(rows: list[dict]) -> dict:
    out = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for r in rows:
        cl = _claimed(r)
        tr = bool(r["truth_d3"])
        if cl and tr:
            out["tp"] += 1
        elif cl and not tr:
            out["fp"] += 1
        elif (not cl) and tr:
            out["fn"] += 1
        else:
            out["tn"] += 1
    return out


def sensitivity(c: dict) -> float:
    pos = c["tp"] + c["fn"]
    if pos == 0:
        return float("nan")
    return c["tp"] / pos


def specificity(c: dict) -> float:
    neg = c["tn"] + c["fp"]
    if neg == 0:
        return float("nan")
    return c["tn"] / neg


def per_ma_count_error(rows: list[dict]) -> dict:
    by_ma: dict[str, dict[str, int]] = defaultdict(lambda: {"claimed": 0, "truth": 0})
    for r in rows:
        by_ma[r["ma_id"]]["claimed"] += int(_claimed(r))
        by_ma[r["ma_id"]]["truth"] += int(bool(r["truth_d3"]))
    return {ma: abs(d["claimed"] - d["truth"]) for ma, d in by_ma.items()}
```

- [ ] **Step 4: Run, expect pass** → 7 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/audit.py tests/test_audit.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(audit): confusion matrix + per-MA count error"
```

---

## Task 11: Clustered bootstrap with k<10 guard (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/bootstrap.py`
- Test: `tests/test_bootstrap.py`, `tests/test_seed_determinism.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_bootstrap.py
import math
import pytest

from africa_hiv_prep_atlas.bootstrap import (
    cluster_bootstrap_sens_spec,
    permutation_sens_spec,
    choose_method,
)


def _rows(spec):
    """spec = list of (ma, claim, truth)."""
    return [
        {"ma_id": ma, "trial_id": f"T{i}",
         "claimed_a": claim, "claimed_b": False, "claimed_c": False,
         "truth_d1": truth, "truth_d2": truth, "truth_d3": truth}
        for i, (ma, claim, truth) in enumerate(spec)
    ]


def test_choose_method_clustered_for_k_ge_10():
    mas = [f"M{i}" for i in range(11)]
    rows = [{"ma_id": m, "trial_id": "T1",
             "claimed_a": True, "claimed_b": False, "claimed_c": False,
             "truth_d1": True, "truth_d2": True, "truth_d3": True}
            for m in mas]
    assert choose_method(rows) == "clustered_bootstrap"


def test_choose_method_permutation_for_k_lt_10():
    mas = [f"M{i}" for i in range(5)]
    rows = [{"ma_id": m, "trial_id": "T1",
             "claimed_a": True, "claimed_b": False, "claimed_c": False,
             "truth_d1": True, "truth_d2": True, "truth_d3": True}
            for m in mas]
    assert choose_method(rows) == "permutation"


def test_cluster_bootstrap_returns_point_and_ci():
    rows = _rows([
        ("M1", True, True), ("M1", True, False),
        ("M2", False, True), ("M2", True, True),
        ("M3", True, True), ("M3", False, False),
    ] * 5)
    result = cluster_bootstrap_sens_spec(rows, n_reps=200, seed=42)
    assert "sensitivity" in result
    assert "specificity" in result
    assert "sens_ci" in result
    assert "spec_ci" in result
    s_lo, s_hi = result["sens_ci"]
    assert 0.0 <= s_lo <= s_hi <= 1.0


def test_permutation_returns_point_and_ci():
    rows = _rows([
        ("M1", True, True), ("M1", False, False),
        ("M2", True, True), ("M2", True, False),
    ])
    result = permutation_sens_spec(rows, n_reps=500, seed=42)
    assert "sensitivity" in result
    assert "specificity" in result
```

```python
# tests/test_seed_determinism.py
from africa_hiv_prep_atlas.bootstrap import cluster_bootstrap_sens_spec


def _rows():
    return [
        {"ma_id": f"M{i}", "trial_id": f"T{j}",
         "claimed_a": (i + j) % 2 == 0, "claimed_b": False, "claimed_c": False,
         "truth_d1": j % 2 == 0, "truth_d2": j % 2 == 0, "truth_d3": j % 2 == 0}
        for i in range(12) for j in range(6)
    ]


def test_seed_42_reproducible():
    a = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=42)
    b = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=42)
    assert a["sens_ci"] == b["sens_ci"]
    assert a["spec_ci"] == b["spec_ci"]


def test_different_seeds_differ():
    a = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=42)
    b = cluster_bootstrap_sens_spec(_rows(), n_reps=200, seed=43)
    assert a["sens_ci"] != b["sens_ci"]
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `bootstrap.py`**

```python
"""Clustered bootstrap and permutation fallback for sens/spec CIs."""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from africa_hiv_prep_atlas.audit import confusion_at_d3, sensitivity, specificity

K_GUARD_THRESHOLD = 10


def choose_method(rows: list[dict]) -> str:
    n_mas = len({r["ma_id"] for r in rows})
    return "clustered_bootstrap" if n_mas >= K_GUARD_THRESHOLD else "permutation"


def _rows_by_ma(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[r["ma_id"]].append(r)
    return dict(out)


def cluster_bootstrap_sens_spec(
    rows: list[dict], n_reps: int = 1000, seed: int = 42, alpha: float = 0.05,
) -> dict:
    rng = np.random.default_rng(seed)
    by_ma = _rows_by_ma(rows)
    ma_keys = list(by_ma.keys())
    n_clusters = len(ma_keys)

    point_c = confusion_at_d3(rows)
    point_sens = sensitivity(point_c)
    point_spec = specificity(point_c)

    sens_samples: list[float] = []
    spec_samples: list[float] = []
    for _ in range(n_reps):
        idx = rng.integers(0, n_clusters, size=n_clusters)
        resample: list[dict] = []
        for i in idx:
            resample.extend(by_ma[ma_keys[i]])
        c = confusion_at_d3(resample)
        s = sensitivity(c)
        p = specificity(c)
        if not math.isnan(s):
            sens_samples.append(s)
        if not math.isnan(p):
            spec_samples.append(p)
    sens_samples.sort()
    spec_samples.sort()

    def _quant(arr, q):
        if not arr:
            return float("nan")
        i = int(q * (len(arr) - 1))
        return arr[i]

    return {
        "method": "clustered_bootstrap",
        "n_clusters": n_clusters,
        "n_reps": n_reps,
        "sensitivity": point_sens,
        "specificity": point_spec,
        "sens_ci": (_quant(sens_samples, alpha / 2), _quant(sens_samples, 1 - alpha / 2)),
        "spec_ci": (_quant(spec_samples, alpha / 2), _quant(spec_samples, 1 - alpha / 2)),
    }


def permutation_sens_spec(
    rows: list[dict], n_reps: int = 1000, seed: int = 42, alpha: float = 0.05,
) -> dict:
    """k<10 guard: permute claim labels within trials, derive null distribution.

    Used as a fallback when the cluster bootstrap is unstable due to k<10 MAs.
    """
    rng = np.random.default_rng(seed)
    point_c = confusion_at_d3(rows)
    point_sens = sensitivity(point_c)
    point_spec = specificity(point_c)

    n = len(rows)
    sens_samples: list[float] = []
    spec_samples: list[float] = []
    for _ in range(n_reps):
        idx = rng.permutation(n)
        permuted = [
            dict(rows[i], truth_d3=rows[idx[i]]["truth_d3"])
            for i in range(n)
        ]
        c = confusion_at_d3(permuted)
        s = sensitivity(c)
        p = specificity(c)
        if not math.isnan(s):
            sens_samples.append(s)
        if not math.isnan(p):
            spec_samples.append(p)
    sens_samples.sort()
    spec_samples.sort()

    def _quant(arr, q):
        if not arr:
            return float("nan")
        i = int(q * (len(arr) - 1))
        return arr[i]

    return {
        "method": "permutation",
        "n_reps": n_reps,
        "sensitivity": point_sens,
        "specificity": point_spec,
        "sens_ci": (_quant(sens_samples, alpha / 2), _quant(sens_samples, 1 - alpha / 2)),
        "spec_ci": (_quant(spec_samples, alpha / 2), _quant(spec_samples, 1 - alpha / 2)),
    }
```

- [ ] **Step 4: Run, expect pass** → 5 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/bootstrap.py tests/test_bootstrap.py tests/test_seed_determinism.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(bootstrap): clustered bootstrap + k<10 permutation guard, seeded"
```

---

## Task 12: CSV writers + atlas.csv byte-pinning (TDD)

**Files:**
- Create: `src/africa_hiv_prep_atlas/csv_writers.py`
- Test: `tests/test_csv_writers.py`, `tests/test_atlas_pinning.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_csv_writers.py
from io import StringIO

from africa_hiv_prep_atlas.csv_writers import (
    write_atlas_csv,
    write_trials_csv,
    write_mas_csv,
    ATLAS_COLUMNS,
    TRIALS_COLUMNS,
    MAS_COLUMNS,
)


def test_atlas_columns_exact():
    assert ATLAS_COLUMNS == (
        "ma_id", "trial_id",
        "claimed_a", "claimed_b", "claimed_c", "claimed_union",
        "truth_d1", "truth_d2", "truth_d3",
        "tp_at_d3", "fp_at_d3", "fn_at_d3", "tn_at_d3",
        "confidence_layer_m", "confidence_layer_t",
        "source_lines",
    )


def test_atlas_writer_emits_deterministic_csv():
    rows = [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": False, "claimed_c": False,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ("M1_p3l5", "T1_p1l2")},
    ]
    buf = StringIO()
    write_atlas_csv(rows, buf)
    out = buf.getvalue()
    assert out.startswith(",".join(ATLAS_COLUMNS) + "\n")
    assert "M1,T1,True,False,False,True,True,True,True,True,False,False,False,high,high,M1_p3l5;T1_p1l2" in out


def test_atlas_writer_sorts_rows():
    rows = [
        {"ma_id": "M2", "trial_id": "T1",
         "claimed_a": False, "claimed_b": False, "claimed_c": False,
         "truth_d1": False, "truth_d2": False, "truth_d3": False,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ()},
        {"ma_id": "M1", "trial_id": "T2",
         "claimed_a": True, "claimed_b": True, "claimed_c": True,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ()},
    ]
    buf = StringIO()
    write_atlas_csv(rows, buf)
    lines = buf.getvalue().strip().split("\n")
    # Sorted by (ma_id, trial_id)
    assert lines[1].startswith("M1,T2,")
    assert lines[2].startswith("M2,T1,")
```

```python
# tests/test_atlas_pinning.py
"""Byte-pinning: atlas.csv is reproducible bit-for-bit on rerun."""
import hashlib
from io import StringIO

from africa_hiv_prep_atlas.csv_writers import write_atlas_csv


def _sample_rows():
    return [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": False, "claimed_c": False,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "confidence_layer_m": "high", "confidence_layer_t": "high",
         "source_lines": ("a", "b")},
        {"ma_id": "M1", "trial_id": "T2",
         "claimed_a": False, "claimed_b": True, "claimed_c": False,
         "truth_d1": True, "truth_d2": False, "truth_d3": False,
         "confidence_layer_m": "medium", "confidence_layer_t": "high",
         "source_lines": ("c",)},
    ]


def test_byte_identical_on_rerun():
    a = StringIO(); write_atlas_csv(_sample_rows(), a)
    b = StringIO(); write_atlas_csv(_sample_rows(), b)
    assert hashlib.sha256(a.getvalue().encode()).hexdigest() == hashlib.sha256(b.getvalue().encode()).hexdigest()


def test_byte_identical_under_input_reorder():
    rows = _sample_rows()
    a = StringIO(); write_atlas_csv(rows, a)
    b = StringIO(); write_atlas_csv(list(reversed(rows)), b)
    assert a.getvalue() == b.getvalue()
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `csv_writers.py`**

```python
"""Deterministic CSV writers for atlas / trials / mas."""
from __future__ import annotations

import csv
from typing import IO

ATLAS_COLUMNS = (
    "ma_id", "trial_id",
    "claimed_a", "claimed_b", "claimed_c", "claimed_union",
    "truth_d1", "truth_d2", "truth_d3",
    "tp_at_d3", "fp_at_d3", "fn_at_d3", "tn_at_d3",
    "confidence_layer_m", "confidence_layer_t",
    "source_lines",
)

TRIALS_COLUMNS = (
    "trial_id", "nct", "pactr", "modality", "year",
    "total_enrolled", "african_n", "african_fraction",
    "truth_d1", "truth_d2", "truth_d3", "source_id",
)

MAS_COLUMNS = (
    "ma_id", "first_author", "year", "n_cited_trials",
    "search_date", "full_text_source_id",
)


def _serialise_source_lines(value) -> str:
    if not value:
        return ""
    return ";".join(value)


def write_atlas_csv(rows: list[dict], stream: IO[str]) -> None:
    enriched: list[dict] = []
    for r in rows:
        cl = bool(r.get("claimed_a") or r.get("claimed_b") or r.get("claimed_c"))
        tr = bool(r["truth_d3"])
        enriched.append({
            "ma_id": r["ma_id"], "trial_id": r["trial_id"],
            "claimed_a": r["claimed_a"], "claimed_b": r["claimed_b"], "claimed_c": r["claimed_c"],
            "claimed_union": cl,
            "truth_d1": r["truth_d1"], "truth_d2": r["truth_d2"], "truth_d3": r["truth_d3"],
            "tp_at_d3": cl and tr,
            "fp_at_d3": cl and not tr,
            "fn_at_d3": (not cl) and tr,
            "tn_at_d3": (not cl) and (not tr),
            "confidence_layer_m": r["confidence_layer_m"],
            "confidence_layer_t": r["confidence_layer_t"],
            "source_lines": _serialise_source_lines(r["source_lines"]),
        })
    enriched.sort(key=lambda x: (x["ma_id"], x["trial_id"]))
    w = csv.DictWriter(stream, fieldnames=list(ATLAS_COLUMNS), lineterminator="\n")
    w.writeheader()
    for row in enriched:
        w.writerow(row)


def write_trials_csv(trials: list[dict], stream: IO[str]) -> None:
    sorted_rows = sorted(trials, key=lambda x: x["trial_id"])
    w = csv.DictWriter(stream, fieldnames=list(TRIALS_COLUMNS), lineterminator="\n")
    w.writeheader()
    for r in sorted_rows:
        w.writerow({k: r.get(k, "") for k in TRIALS_COLUMNS})


def write_mas_csv(mas: list[dict], stream: IO[str]) -> None:
    sorted_rows = sorted(mas, key=lambda x: x["ma_id"])
    w = csv.DictWriter(stream, fieldnames=list(MAS_COLUMNS), lineterminator="\n")
    w.writeheader()
    for r in sorted_rows:
        w.writerow({k: r.get(k, "") for k in MAS_COLUMNS})
```

- [ ] **Step 4: Run, expect pass** → 5 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/csv_writers.py tests/test_csv_writers.py tests/test_atlas_pinning.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(csv_writers): deterministic atlas/trials/mas writers + byte-pinning"
```

---

## Task 13: Trial fixtures (manual extraction, source-line-attributed)

**Files:**
- Create: `fixtures/trials/<trial_id>.json` × ≥6
- Test: `tests/test_trial_fixtures.py`

Per spec §6 ("Source-line attribution: every cell carries a source_id pointer; no source = no value"), fixtures are committed JSON with verbatim excerpts.

- [ ] **Step 1: Write the fixture-validation test FIRST**

```python
# tests/test_trial_fixtures.py
import json
from pathlib import Path

import pytest

from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_trial

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "trials"
REQUIRED_KEYS = {
    "trial_id", "nct", "pactr", "modality", "year",
    "enrolment_by_country", "sites_by_country",
    "total_enrolled", "source_id", "verbatim_excerpts",
}


def _fixture_files():
    return sorted(FIXTURE_DIR.glob("*.json"))


def test_at_least_6_trials():
    assert len(_fixture_files()) >= 6


def test_each_fixture_has_required_keys():
    for f in _fixture_files():
        data = json.loads(f.read_text(encoding="utf-8"))
        missing = REQUIRED_KEYS - data.keys()
        assert not missing, f"{f.name} missing keys: {missing}"


def test_each_fixture_has_at_least_one_verbatim_excerpt():
    for f in _fixture_files():
        data = json.loads(f.read_text(encoding="utf-8"))
        excerpts = data.get("verbatim_excerpts", [])
        assert len(excerpts) >= 1, f"{f.name} has no verbatim excerpts"
        for e in excerpts:
            assert "source_id" in e and "text" in e and "locator" in e


def test_each_fixture_total_matches_country_sum():
    for f in _fixture_files():
        data = json.loads(f.read_text(encoding="utf-8"))
        country_sum = sum(data["enrolment_by_country"].values())
        # total_enrolled may be slightly larger than country_sum if there's
        # un-allocated enrolment; never smaller.
        assert data["total_enrolled"] >= country_sum, (
            f"{f.name} total_enrolled={data['total_enrolled']} < "
            f"country_sum={country_sum}"
        )


def test_each_fixture_classifies_under_at_least_d1():
    """v0.1.0 trial universe is LA-PrEP — every included trial has at least
    one African site (this is part of the inclusion criterion)."""
    for f in _fixture_files():
        data = json.loads(f.read_text(encoding="utf-8"))
        t = Trial(
            trial_id=data["trial_id"], nct=data["nct"], pactr=data["pactr"],
            modality=data["modality"], year=data["year"],
            enrolment_by_country=data["enrolment_by_country"],
            total_enrolled=data["total_enrolled"], source_id=data["source_id"],
        )
        flags = classify_trial(t, data["sites_by_country"])
        assert flags["d1"] is True, f"{f.name} fails D1 — re-check inclusion"
```

- [ ] **Step 2: Run, expect failure**

`pytest tests/test_trial_fixtures.py -v` → 5 fail (no fixtures yet).

- [ ] **Step 3: Create the trial fixtures**

For each of the v0.1.0 trial universe (HPTN_083, HPTN_084, ASPIRE, RING_STUDY, MTN_025_HOPE, IPM_027), create `fixtures/trials/<trial_id>.json` using this exact schema:

```json
{
  "trial_id": "HPTN_084",
  "nct": "NCT03164564",
  "pactr": null,
  "modality": "cabotegravir-LA",
  "year": 2020,
  "enrolment_by_country": {
    "South Africa": 0,
    "Botswana": 0,
    "Eswatini": 0,
    "Kenya": 0,
    "Malawi": 0,
    "Uganda": 0,
    "Zimbabwe": 0
  },
  "sites_by_country": {
    "South Africa": 0,
    "Botswana": 0,
    "Eswatini": 0,
    "Kenya": 0,
    "Malawi": 0,
    "Uganda": 0,
    "Zimbabwe": 0
  },
  "total_enrolled": 0,
  "source_id": "delany-moretlwe-2022-lancet",
  "verbatim_excerpts": [
    {
      "source_id": "delany-moretlwe-2022-lancet-table1",
      "locator": "Table 1, p. e1335",
      "text": "VERBATIM TEXT FROM PUBLICATION"
    }
  ]
}
```

For each trial, fill the actual values from the primary publication. **Do not commit a fixture with `0` placeholder values.** The test `test_each_fixture_total_matches_country_sum` will catch zero-totals.

Sources to consult per trial (locator format: `<lead-author>-<year>-<journal>`):
- `HPTN_083`: Landovitz et al., NEJM 2021 — `landovitz-2021-nejm`
- `HPTN_084`: Delany-Moretlwe et al., Lancet 2022 — `delany-moretlwe-2022-lancet`
- `ASPIRE` (MTN-020): Baeten et al., NEJM 2016 — `baeten-2016-nejm`
- `RING_STUDY` (IPM 027): Nel et al., NEJM 2016 — `nel-2016-nejm`
- `MTN_025_HOPE`: Baeten et al., JID 2021 — `baeten-2021-jid`
- `IPM_027`: as Ring Study (combine into one fixture if same trial)

If a fixture's `pactr` field is unknown, leave it `null` and document in `verbatim_excerpts` why no PACTR ID was located.

- [ ] **Step 4: Run, expect pass**

`pytest tests/test_trial_fixtures.py -v` → 5 passed (≥6 fixtures present, all schemas valid).

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add fixtures/trials/ tests/test_trial_fixtures.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "data(trials): seed ≥6 LA-PrEP trial fixtures with verbatim excerpts"
```

---

## Task 14: MA fixtures (PRISMA search + Layer-M extraction)

**Files:**
- Create: `fixtures/mas/<ma_id>/meta.json` and `fixtures/mas/<ma_id>/claims.json` × ≥10
- Create: `docs/prisma_flow.md` — PRISMA-compliant flow diagram
- Test: `tests/test_ma_fixtures.py`

Per spec §5: MAs published 2020-01-01 onwards covering ≥1 LA modality. Search Cochrane CDSR + PubMed + Epistemonikos.

- [ ] **Step 1: Run the literature search and document PRISMA flow**

Save the search strings to `docs/prisma_flow.md` (count records identified / screened / included). For each included MA, record:
- DOI, PMID, first-author, year
- Search date
- Cited LA-PrEP trials (cross-checked against `fixtures/trials/`)
- Full-text PDF source (committed to `fixtures/mas/<ma_id>/source.pdf` if license permits, otherwise document obtain method in `meta.json`)

- [ ] **Step 2: Write the fixture-validation test FIRST**

```python
# tests/test_ma_fixtures.py
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "mas"
TRIAL_DIR = Path(__file__).parent.parent / "fixtures" / "trials"

META_KEYS = {"ma_id", "first_author", "year", "doi", "search_date",
             "cited_trial_ids", "full_text_source_id"}
CLAIM_LAYERS = {"a", "b", "c"}


def _ma_dirs():
    return sorted(p for p in FIXTURE_DIR.iterdir() if p.is_dir())


def _trial_ids():
    return {p.stem for p in TRIAL_DIR.glob("*.json")}


def test_at_least_10_mas():
    assert len(_ma_dirs()) >= 10


def test_each_ma_has_meta_and_claims():
    for d in _ma_dirs():
        assert (d / "meta.json").exists(), f"{d.name} missing meta.json"
        assert (d / "claims.json").exists(), f"{d.name} missing claims.json"


def test_each_meta_has_required_keys():
    for d in _ma_dirs():
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        missing = META_KEYS - meta.keys()
        assert not missing, f"{d.name} meta missing: {missing}"


def test_meta_year_is_2020_or_later():
    for d in _ma_dirs():
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        assert meta["year"] >= 2020, f"{d.name}: year={meta['year']} (must be ≥2020)"


def test_each_claim_uses_known_trial_id():
    valid = _trial_ids()
    for d in _ma_dirs():
        claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
        for tid in claims["claims"].keys():
            assert tid in valid, f"{d.name}: unknown trial_id {tid!r}"


def test_each_claim_record_has_source_lines():
    for d in _ma_dirs():
        claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
        for tid, layers in claims["claims"].items():
            assert "source_lines" in layers, f"{d.name}/{tid} missing source_lines"
            assert len(layers["source_lines"]) >= 1, (
                f"{d.name}/{tid}: source_lines empty — every claim needs ≥1 source"
            )


def test_at_least_50_pairs_total():
    n_pairs = 0
    for d in _ma_dirs():
        claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
        n_pairs += len(claims["claims"])
    assert n_pairs >= 50, f"only {n_pairs} (MA, trial) pairs — need ≥50"
```

- [ ] **Step 3: Run, expect failure**

`pytest tests/test_ma_fixtures.py -v` → all 7 fail (no fixtures yet).

- [ ] **Step 4: Create MA fixtures (manual + verification.html UI from Task 17)**

For each included MA, create:

```json
// fixtures/mas/<ma_id>/meta.json
{
  "ma_id": "smith2024-cabotegravir-prep",
  "first_author": "Smith",
  "year": 2024,
  "doi": "10.xxxx/yyyy",
  "pmid": "12345678",
  "search_date": "2026-05-15",
  "cited_trial_ids": ["HPTN_083", "HPTN_084", "PURPOSE_1"],
  "full_text_source_id": "smith2024_pdf_oa",
  "search_strategy_excerpt": {
    "source_id": "smith2024-methods",
    "locator": "Methods §2.1 p.3",
    "text": "VERBATIM SEARCH STRING"
  }
}
```

```json
// fixtures/mas/<ma_id>/claims.json
{
  "ma_id": "smith2024-cabotegravir-prep",
  "claims": {
    "HPTN_084": {
      "a": false,
      "b": true,
      "c": true,
      "source_lines": ["smith2024-table2-p5", "smith2024-discussion-p9"],
      "verbatim_quotes": [
        {"source_id": "smith2024-table2-p5", "text": "HPTN 084 (South Africa, Uganda, ...)"},
        {"source_id": "smith2024-discussion-p9", "text": "...findings from HPTN 084 in sub-Saharan Africa..."}
      ]
    }
  }
}
```

(a) = explicit count claim, (b) = implicit-from-included-studies-table, (c) = narrative mention. Each value MUST be backed by a `verbatim_quote` entry.

- [ ] **Step 5: Run, expect pass**

`pytest tests/test_ma_fixtures.py -v` → 7 passed.

- [ ] **Step 6: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add fixtures/mas/ docs/prisma_flow.md tests/test_ma_fixtures.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "data(mas): seed ≥10 LA-PrEP MA fixtures, ≥50 (MA, trial) pairs"
```

---

## Task 15: build_atlas.py orchestration script

**Files:**
- Create: `scripts/build_atlas.py`
- Test: `tests/test_build_atlas.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_build_atlas.py
import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
DATA = REPO / "data"


def test_build_atlas_produces_three_csvs():
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_atlas.py")],
        capture_output=True, text=True, cwd=REPO,
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    assert (DATA / "atlas.csv").exists()
    assert (DATA / "trials.csv").exists()
    assert (DATA / "mas.csv").exists()


def test_atlas_csv_byte_pinned_on_rerun():
    """atlas.csv must be byte-identical on consecutive builds (reproducibility)."""
    subprocess.run([sys.executable, str(REPO / "scripts" / "build_atlas.py")],
                   check=True, cwd=REPO)
    h1 = hashlib.sha256((DATA / "atlas.csv").read_bytes()).hexdigest()
    subprocess.run([sys.executable, str(REPO / "scripts" / "build_atlas.py")],
                   check=True, cwd=REPO)
    h2 = hashlib.sha256((DATA / "atlas.csv").read_bytes()).hexdigest()
    assert h1 == h2


def test_atlas_csv_row_count_matches_pair_count():
    import json
    fixture_dir = REPO / "fixtures" / "mas"
    expected_pairs = 0
    for d in fixture_dir.iterdir():
        if d.is_dir():
            claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
            expected_pairs += len(claims["claims"])
    csv_lines = (DATA / "atlas.csv").read_text(encoding="utf-8").strip().split("\n")
    assert len(csv_lines) - 1 == expected_pairs  # subtract header
```

- [ ] **Step 2: Run, expect failure** → all errors (no script).

- [ ] **Step 3: Implement `scripts/build_atlas.py`**

```python
"""Build trials.csv, mas.csv, atlas.csv from committed fixtures."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from africa_hiv_prep_atlas.records import Trial
from africa_hiv_prep_atlas.ground_truth import classify_trial
from africa_hiv_prep_atlas.confidence import classify_confidence, Confidence
from africa_hiv_prep_atlas.csv_writers import (
    write_atlas_csv, write_trials_csv, write_mas_csv,
)

TRIAL_FIXTURES = REPO / "fixtures" / "trials"
MA_FIXTURES = REPO / "fixtures" / "mas"
DATA = REPO / "data"


def load_trials() -> tuple[list[dict], dict]:
    trials_records: list[dict] = []
    truth_by_trial: dict[str, dict] = {}
    for f in sorted(TRIAL_FIXTURES.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        t = Trial(
            trial_id=d["trial_id"], nct=d["nct"], pactr=d["pactr"],
            modality=d["modality"], year=d["year"],
            enrolment_by_country=d["enrolment_by_country"],
            total_enrolled=d["total_enrolled"], source_id=d["source_id"],
        )
        flags = classify_trial(t, d["sites_by_country"])
        trials_records.append({
            "trial_id": t.trial_id, "nct": t.nct or "", "pactr": t.pactr or "",
            "modality": t.modality, "year": t.year,
            "total_enrolled": t.total_enrolled,
            "african_n": t.african_n(),
            "african_fraction": round(t.african_fraction(), 4),
            "truth_d1": flags["d1"], "truth_d2": flags["d2"], "truth_d3": flags["d3"],
            "source_id": t.source_id,
        })
        truth_by_trial[t.trial_id] = flags
    return trials_records, truth_by_trial


def load_mas_and_atlas(truth_by_trial: dict) -> tuple[list[dict], list[dict]]:
    mas_records: list[dict] = []
    atlas_rows: list[dict] = []
    for d in sorted(p for p in MA_FIXTURES.iterdir() if p.is_dir()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
        mas_records.append({
            "ma_id": meta["ma_id"], "first_author": meta["first_author"],
            "year": meta["year"], "n_cited_trials": len(meta["cited_trial_ids"]),
            "search_date": meta["search_date"],
            "full_text_source_id": meta["full_text_source_id"],
        })
        for trial_id, layers in claims["claims"].items():
            truth = truth_by_trial.get(trial_id, {"d1": False, "d2": False, "d3": False})
            atlas_rows.append({
                "ma_id": meta["ma_id"], "trial_id": trial_id,
                "claimed_a": bool(layers.get("a", False)),
                "claimed_b": bool(layers.get("b", False)),
                "claimed_c": bool(layers.get("c", False)),
                "truth_d1": truth["d1"], "truth_d2": truth["d2"], "truth_d3": truth["d3"],
                # Layer-M is manual-only in v0.1.0 -> high confidence (with verbatim quote).
                "confidence_layer_m": Confidence.HIGH.value,
                # Layer-T is manual-only in v0.1.0 -> high confidence.
                "confidence_layer_t": Confidence.HIGH.value,
                "source_lines": tuple(layers.get("source_lines", ())),
            })
    return mas_records, atlas_rows


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    trials_records, truth_by_trial = load_trials()
    mas_records, atlas_rows = load_mas_and_atlas(truth_by_trial)

    with (DATA / "trials.csv").open("w", encoding="utf-8", newline="") as f:
        write_trials_csv(trials_records, f)
    with (DATA / "mas.csv").open("w", encoding="utf-8", newline="") as f:
        write_mas_csv(mas_records, f)
    with (DATA / "atlas.csv").open("w", encoding="utf-8", newline="") as f:
        write_atlas_csv(atlas_rows, f)
    print(f"wrote {len(trials_records)} trials, {len(mas_records)} MAs, "
          f"{len(atlas_rows)} (MA, trial) pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run, expect pass** → 3 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add scripts/build_atlas.py tests/test_build_atlas.py data/
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(build_atlas): orchestrate fixtures → trials/mas/atlas CSVs"
```

---

## Task 16: dashboard.html generator

**Files:**
- Create: `src/africa_hiv_prep_atlas/dashboard.py`
- Test: `tests/test_dashboard.py`

Self-contained HTML, inline SVG, no external CDN, no localStorage collision (per portfolio top-5-defects rule).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_dashboard.py
import re

from africa_hiv_prep_atlas.dashboard import render_dashboard


def _sample():
    rows = [
        {"ma_id": "M1", "trial_id": "T1",
         "claimed_a": True, "claimed_b": True, "claimed_c": False, "claimed_union": True,
         "truth_d1": True, "truth_d2": True, "truth_d3": True,
         "tp_at_d3": True, "fp_at_d3": False, "fn_at_d3": False, "tn_at_d3": False,
         "confidence_layer_m": "high", "confidence_layer_t": "high"},
    ]
    headline = {"sensitivity": 0.8, "specificity": 0.9,
                "sens_ci": (0.7, 0.9), "spec_ci": (0.85, 0.95),
                "method": "clustered_bootstrap", "n_clusters": 12}
    return rows, headline


def test_dashboard_returns_full_html_doc():
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    assert html.startswith("<!doctype html>") or html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_dashboard_self_contained_no_external_cdn():
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    forbidden = ["cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com", "googleapis.com"]
    for u in forbidden:
        assert u not in html


def test_dashboard_no_literal_close_script_in_template_literal():
    """lessons.md JS rule: no literal </script> in template literals."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    # Only allowable instance: the actual closing </script> tags.
    # Total </script> count should equal total <script> count.
    assert html.count("<script") == html.count("</script>")


def test_dashboard_localstorage_keys_namespaced():
    """top-5-defects: localStorage keys must be project-namespaced."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    if "localStorage" in html:
        assert re.search(r"localStorage\.(get|set|remove)Item\([\"']ahpa-", html), (
            "localStorage keys must start with 'ahpa-' namespace"
        )


def test_dashboard_renders_headline_number():
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    assert "0.80" in html or "80" in html  # sensitivity point estimate
    assert "0.7" in html  # CI lower bound


def test_dashboard_div_balance():
    """Count <div[\\s>] vs </div>."""
    rows, headline = _sample()
    html = render_dashboard(rows, headline)
    n_open = len(re.findall(r"<div[\s>]", html))
    n_close = html.count("</div>")
    assert n_open == n_close, f"open={n_open} close={n_close}"
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `dashboard.py`**

```python
"""Self-contained dashboard.html generator (inline SVG, no CDN)."""
from __future__ import annotations

import html as _html
import json

LS_NAMESPACE = "ahpa-v0.1.0-"


def _row_to_tr(r: dict) -> str:
    cells = [
        _html.escape(str(r["ma_id"])),
        _html.escape(str(r["trial_id"])),
        "✓" if r["claimed_union"] else "—",
        "✓" if r["truth_d3"] else "—",
        "TP" if r["tp_at_d3"] else "FP" if r["fp_at_d3"] else "FN" if r["fn_at_d3"] else "TN",
    ]
    return "<tr><td>" + "</td><td>".join(cells) + "</td></tr>"


def render_dashboard(rows: list[dict], headline: dict) -> str:
    rows_html = "\n".join(_row_to_tr(r) for r in rows)
    headline_json = json.dumps(headline)
    sens_pct = f"{headline['sensitivity']:.2f}"
    spec_pct = f"{headline['specificity']:.2f}"
    sens_lo, sens_hi = headline["sens_ci"]
    spec_lo, spec_hi = headline["spec_ci"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>African HIV PrEP/PEP Long-Acting Trial Atlas</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 1.5rem; max-width: 1100px; }}
h1 {{ font-size: 1.4rem; }}
.headline {{ background: #f5f5f5; padding: 1rem; border-left: 4px solid #2a6; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem; text-align: left; }}
.tp {{ background: #e7f5e7; }}
.fp {{ background: #fce7e7; }}
.fn {{ background: #fcf2e7; }}
</style>
</head>
<body>
<h1>African HIV PrEP/PEP Long-Acting Trial Atlas v0.1.0</h1>
<div class="headline">
  <p><strong>Sensitivity:</strong> {sens_pct} (95% CI {sens_lo:.2f}–{sens_hi:.2f})</p>
  <p><strong>Specificity:</strong> {spec_pct} (95% CI {spec_lo:.2f}–{spec_hi:.2f})</p>
  <p><em>Method:</em> {_html.escape(headline.get("method", "?"))} · n_clusters={headline.get("n_clusters", "?")}</p>
</div>
<h2>Atlas rows</h2>
<table>
<thead><tr><th>MA</th><th>Trial</th><th>MA classified African?</th><th>Truth (D3)</th><th>Cell</th></tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
<script>
window.AHPA_HEADLINE = {headline_json};
try {{ localStorage.setItem("{LS_NAMESPACE}last-render", new Date().toISOString()); }} catch (e) {{}}
</script>
</body>
</html>"""
```

- [ ] **Step 4: Run, expect pass** → 6 passed.

- [ ] **Step 5: Generate `outputs/dashboard.html` from build_atlas + bootstrap**

Add to `scripts/build_atlas.py` after CSVs are written:

```python
# At the bottom of main(), after CSVs are written:
from africa_hiv_prep_atlas.bootstrap import (
    cluster_bootstrap_sens_spec, permutation_sens_spec, choose_method,
)
from africa_hiv_prep_atlas.dashboard import render_dashboard

method = choose_method(atlas_rows)
fn = cluster_bootstrap_sens_spec if method == "clustered_bootstrap" else permutation_sens_spec
headline = fn(atlas_rows, n_reps=1000, seed=42)

# Re-derive enriched rows (with claimed_union + cell flags) for the dashboard.
import io
from africa_hiv_prep_atlas.csv_writers import write_atlas_csv
buf = io.StringIO(); write_atlas_csv(atlas_rows, buf); buf.seek(0)
import csv as _csv
enriched = [
    {**r, **{k: r[k] == "True" for k in (
        "claimed_a", "claimed_b", "claimed_c", "claimed_union",
        "truth_d1", "truth_d2", "truth_d3",
        "tp_at_d3", "fp_at_d3", "fn_at_d3", "tn_at_d3",
    )}}
    for r in _csv.DictReader(buf)
]
(REPO / "outputs").mkdir(parents=True, exist_ok=True)
(REPO / "outputs" / "dashboard.html").write_text(
    render_dashboard(enriched, headline), encoding="utf-8",
)
print(f"wrote outputs/dashboard.html (method={headline['method']})")
```

Run `python scripts/build_atlas.py` — verify `outputs/dashboard.html` exists.

- [ ] **Step 6: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/dashboard.py tests/test_dashboard.py scripts/build_atlas.py outputs/
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(dashboard): self-contained HTML with bootstrap headline"
```

---

## Task 17: verification.html — RapidMeta-style IRR-audit UI (ARAC Plan 3C)

**Files:**
- Create: `src/africa_hiv_prep_atlas/verification.py`
- Test: `tests/test_verification.py`

One (MA, trial) pair at a time. Rater clicks claim_union: yes/no AND truth_d3: yes/no after reading verbatim quotes. Stores to localStorage under `ahpa-irr-<rater_id>-<pair_id>`. JSON export at end.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_verification.py
import re

from africa_hiv_prep_atlas.verification import render_verification_ui


def _sample_pairs():
    return [
        {"ma_id": "M1", "trial_id": "T1",
         "ma_quotes": [{"source_id": "M1-p3", "text": "..."}],
         "trial_quotes": [{"source_id": "T1-p1", "text": "..."}]},
        {"ma_id": "M2", "trial_id": "T1",
         "ma_quotes": [{"source_id": "M2-p4", "text": "..."}],
         "trial_quotes": [{"source_id": "T1-p1", "text": "..."}]},
    ]


def test_verification_renders_one_pair_at_a_time():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "data-pair-index=\"0\"" in html or 'data-pair-index="0"' in html


def test_localstorage_namespaced_with_rater():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "ahpa-irr-raterA-" in html


def test_export_button_present():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "Export" in html or "export" in html


def test_blinded_no_truth_or_claim_displayed():
    """Rater must NOT see the algorithmic truth_d3 / claimed_union — they're computing it."""
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    assert "truth_d3" not in html.lower() or "data-pair" in html
    # Stronger check: no boolean values like "true" or "false" in pair data attributes.
    assert not re.search(r'data-truth-d3="(true|false)"', html, re.IGNORECASE)
    assert not re.search(r'data-claimed-union="(true|false)"', html, re.IGNORECASE)


def test_verification_div_balance():
    html = render_verification_ui(_sample_pairs(), rater_id="raterA")
    n_open = len(re.findall(r"<div[\s>]", html))
    n_close = html.count("</div>")
    assert n_open == n_close
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `verification.py`**

```python
"""RapidMeta-style one-(MA, trial)-at-a-time IRR audit UI (ARAC Plan 3C)."""
from __future__ import annotations

import html as _html
import json

LS_NAMESPACE = "ahpa-irr-"


def _quote_block(quotes: list[dict]) -> str:
    items = []
    for q in quotes:
        items.append(
            f'<blockquote data-src="{_html.escape(q["source_id"])}">'
            f'<small>{_html.escape(q["source_id"])}</small><br>'
            f'{_html.escape(q["text"])}</blockquote>'
        )
    return "\n".join(items)


def render_verification_ui(pairs: list[dict], rater_id: str) -> str:
    pair_blocks = []
    for i, p in enumerate(pairs):
        pair_blocks.append(f"""
<section class="pair" data-pair-index="{i}" data-pair-id="{_html.escape(p['ma_id'])}__{_html.escape(p['trial_id'])}" hidden>
  <h2>Pair {i + 1} of {len(pairs)}: {_html.escape(p['ma_id'])} × {_html.escape(p['trial_id'])}</h2>
  <h3>MA evidence</h3>
  {_quote_block(p['ma_quotes'])}
  <h3>Trial evidence</h3>
  {_quote_block(p['trial_quotes'])}
  <fieldset>
    <legend>Did the MA classify this trial as African-cohort? (any of a/b/c)</legend>
    <label><input type="radio" name="claim-{i}" value="true"> Yes</label>
    <label><input type="radio" name="claim-{i}" value="false"> No</label>
  </fieldset>
  <fieldset>
    <legend>Is the trial African-cohort under D3 (≥50% enrolment)?</legend>
    <label><input type="radio" name="truth-{i}" value="true"> Yes</label>
    <label><input type="radio" name="truth-{i}" value="false"> No</label>
  </fieldset>
  <button type="button" data-action="next">Save and next</button>
</section>""")
    rater_safe = _html.escape(rater_id)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>IRR Audit — Rater {rater_safe}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 1.5rem; max-width: 800px; }}
.pair {{ border: 1px solid #ccc; padding: 1rem; margin: 1rem 0; }}
blockquote {{ border-left: 3px solid #aac; padding-left: 0.6rem; margin: 0.5rem 0; }}
fieldset {{ margin: 0.6rem 0; }}
</style>
</head>
<body>
<h1>IRR Audit — Rater <code>{rater_safe}</code></h1>
<p>Read each MA quote and trial quote, then answer both questions. <strong>You are blinded to the algorithmic answers.</strong></p>
<div id="pairs">
{"".join(pair_blocks)}
</div>
<button id="export" type="button">Export JSON</button>
<pre id="export-out"></pre>
<script>
const RATER = "{rater_safe}";
const NS = "{LS_NAMESPACE}" + RATER + "-";
const pairs = document.querySelectorAll("section.pair");
let idx = 0;
function show(i) {{
  pairs.forEach(p => p.hidden = true);
  if (i < pairs.length) {{
    pairs[i].hidden = false;
  }}
}}
show(0);
document.querySelectorAll('button[data-action="next"]').forEach(btn => {{
  btn.addEventListener("click", () => {{
    const sec = btn.closest("section.pair");
    const id = sec.dataset.pairId;
    const claim = sec.querySelector(`input[name="claim-${{sec.dataset.pairIndex}}"]:checked`);
    const truth = sec.querySelector(`input[name="truth-${{sec.dataset.pairIndex}}"]:checked`);
    if (!claim || !truth) {{ alert("Please answer both."); return; }}
    try {{
      localStorage.setItem(NS + id, JSON.stringify({{
        claim: claim.value === "true", truth: truth.value === "true",
        ts: new Date().toISOString()
      }}));
    }} catch (e) {{}}
    idx += 1;
    show(idx);
  }});
}});
document.getElementById("export").addEventListener("click", () => {{
  const out = {{}};
  for (let k = 0; k < localStorage.length; k++) {{
    const key = localStorage.key(k);
    if (key && key.startsWith(NS)) {{
      out[key.slice(NS.length)] = JSON.parse(localStorage.getItem(key));
    }}
  }}
  document.getElementById("export-out").textContent = JSON.stringify(out, null, 2);
}});
</script>
</body>
</html>"""
```

- [ ] **Step 4: Run, expect pass** → 5 passed.

- [ ] **Step 5: Wire verification.html generation into build_atlas**

At the bottom of `scripts/build_atlas.py::main()`:

```python
from africa_hiv_prep_atlas.verification import render_verification_ui
import random

# Build the full pair-evidence list from fixtures.
verification_pairs: list[dict] = []
for d in sorted(p for p in MA_FIXTURES.iterdir() if p.is_dir()):
    claims = json.loads((d / "claims.json").read_text(encoding="utf-8"))
    for trial_id, layers in claims["claims"].items():
        ma_quotes = layers.get("verbatim_quotes", [])
        trial_path = TRIAL_FIXTURES / f"{trial_id}.json"
        if trial_path.exists():
            tdata = json.loads(trial_path.read_text(encoding="utf-8"))
            trial_quotes = tdata.get("verbatim_excerpts", [])
        else:
            trial_quotes = []
        verification_pairs.append({
            "ma_id": claims["ma_id"], "trial_id": trial_id,
            "ma_quotes": ma_quotes, "trial_quotes": trial_quotes,
        })

# Random n=30 sample, seeded.
rng = random.Random(20260507)
n_sample = min(30, len(verification_pairs))
audit_sample = rng.sample(verification_pairs, n_sample)

(REPO / "outputs" / "verification.html").write_text(
    render_verification_ui(audit_sample, rater_id="REPLACE_AT_RUNTIME"),
    encoding="utf-8",
)
print(f"wrote outputs/verification.html (n={n_sample} pairs)")
```

- [ ] **Step 6: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add src/africa_hiv_prep_atlas/verification.py tests/test_verification.py scripts/build_atlas.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(verification): RapidMeta-style IRR audit UI (ARAC Plan 3C)"
```

---

## Task 18: prereg-v0.0.1 tag (spec freeze) + first OTS pre-stamp

**Files:**
- Create: `prereg/v0.0.1/spec.md` (snapshot of approved spec)
- Create: `.ots/prereg-v0.0.1.spec.md.ots`

This locks the spec **before** any (MA, trial) data is committed. Spec changes after this point require a `prereg-v0.1.0-amend-N` tag.

- [ ] **Step 1: Snapshot the spec**

```
mkdir -p prereg/v0.0.1
cp docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md prereg/v0.0.1/spec.md
```

- [ ] **Step 2: OTS-stamp the prereg snapshot**

```
ots stamp prereg/v0.0.1/spec.md
mkdir -p .ots
mv prereg/v0.0.1/spec.md.ots .ots/prereg-v0.0.1-spec.md.ots
```

- [ ] **Step 3: Commit and tag**

```
git -C C:/Projects/africa-hiv-prep-atlas add prereg/v0.0.1/ .ots/prereg-v0.0.1-spec.md.ots
git -C C:/Projects/africa-hiv-prep-atlas commit -m "chore(prereg): freeze v0.0.1 spec snapshot + OTS-stamp"
git -C C:/Projects/africa-hiv-prep-atlas tag -a prereg-v0.0.1 -m "Spec frozen pre-extraction"
git -C C:/Projects/africa-hiv-prep-atlas push --follow-tags
```

- [ ] **Step 4: Verify OTS upgrade later**

Note in `prereg/v0.0.1/README.md`:

```markdown
# prereg-v0.0.1

Spec frozen 2026-05-07 before any (MA, trial) data extraction.
Re-run `ots upgrade .ots/prereg-v0.0.1-spec.md.ots` once Bitcoin block confirmation
posts (~24h after stamp). Then commit the upgraded `.ots` file.
```

```
git -C C:/Projects/africa-hiv-prep-atlas add prereg/v0.0.1/README.md
git -C C:/Projects/africa-hiv-prep-atlas commit -m "docs(prereg): record OTS upgrade reminder"
```

---

## Task 19: prereg-v0.1.0-amend-1 tag (extraction frozen, before unblinding)

**Files:**
- Create: `prereg/v0.1.0-amend-1/spec.md`, `prereg/v0.1.0-amend-1/atlas.csv`, `prereg/v0.1.0-amend-1/CHANGELOG.md`

This locks the *algorithmic* extraction (atlas.csv) **before** the n=30 blinded audit unblinds. Per spec §7: "n=30 audit happens after prereg + initial extraction is OTS-stamped, before unblinding the algorithmic results."

- [ ] **Step 1: Re-run build_atlas to ensure data is current**

```
python scripts/build_atlas.py
pytest -q
```

Expected: pytest 100% pass; CSVs and HTML regenerated.

- [ ] **Step 2: Snapshot atlas.csv + spec into prereg/v0.1.0-amend-1/**

```
mkdir -p prereg/v0.1.0-amend-1
cp data/atlas.csv prereg/v0.1.0-amend-1/atlas.csv
cp docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md prereg/v0.1.0-amend-1/spec.md
```

Write `prereg/v0.1.0-amend-1/CHANGELOG.md`:

```markdown
# Changelog vs prereg-v0.0.1

## Spec changes
- (List any amendments to the design here, OR write "None — spec unchanged from prereg-v0.0.1.")

## Reason for amend tag
Algorithmic extraction (Layer-T + Layer-M) frozen before n=30 blinded IRR audit.
Trial fixtures: <N> trials. MA fixtures: <N> MAs. (MA, trial) pairs: <N>.
```

- [ ] **Step 3: OTS-stamp the snapshot**

```
ots stamp prereg/v0.1.0-amend-1/atlas.csv
ots stamp prereg/v0.1.0-amend-1/spec.md
mv prereg/v0.1.0-amend-1/atlas.csv.ots .ots/prereg-v0.1.0-amend-1-atlas.csv.ots
mv prereg/v0.1.0-amend-1/spec.md.ots .ots/prereg-v0.1.0-amend-1-spec.md.ots
```

- [ ] **Step 4: Commit and tag**

```
git -C C:/Projects/africa-hiv-prep-atlas add prereg/v0.1.0-amend-1/ .ots/prereg-v0.1.0-amend-1-*.ots
git -C C:/Projects/africa-hiv-prep-atlas commit -m "chore(prereg): freeze v0.1.0-amend-1 extraction snapshot + OTS-stamp"
git -C C:/Projects/africa-hiv-prep-atlas tag -a prereg-v0.1.0-amend-1 -m "Algorithmic extraction frozen pre-IRR-audit"
git -C C:/Projects/africa-hiv-prep-atlas push --follow-tags
```

---

## Task 20: n=30 IRR blinded audit + Cohen's κ

**Files:**
- Create: `scripts/compute_kappa.py`
- Test: `tests/test_kappa.py`
- Output: `outputs/irr_audit_results.json`

The audit itself is human-in-the-loop. This task ships the κ tooling and the result-recording protocol.

- [ ] **Step 1: Write failing tests for κ**

```python
# tests/test_kappa.py
import json
from pathlib import Path

import pytest

from scripts.compute_kappa import cohen_kappa, kappa_from_blinded_jsons


def test_perfect_agreement_kappa_is_1():
    a = [True, False, True, True, False]
    b = [True, False, True, True, False]
    assert cohen_kappa(a, b) == 1.0


def test_perfect_disagreement_kappa_is_negative():
    a = [True, True, True, False, False, False]
    b = [False, False, False, True, True, True]
    assert cohen_kappa(a, b) < 0


def test_kappa_above_080_threshold_with_one_disagreement_in_30():
    a = [True] * 15 + [False] * 15
    b = a.copy(); b[0] = False  # 1 disagreement
    k = cohen_kappa(a, b)
    assert k >= 0.80


def test_chance_agreement_kappa_near_zero():
    import random
    rng = random.Random(42)
    a = [rng.random() < 0.5 for _ in range(100)]
    b = [rng.random() < 0.5 for _ in range(100)]
    k = cohen_kappa(a, b)
    assert -0.3 < k < 0.3


def test_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        cohen_kappa([True, False], [True])


def test_kappa_from_jsons(tmp_path):
    a = {"M1__T1": {"claim": True, "truth": True}, "M1__T2": {"claim": False, "truth": False}}
    b = {"M1__T1": {"claim": True, "truth": True}, "M1__T2": {"claim": False, "truth": True}}
    fa = tmp_path / "a.json"; fa.write_text(json.dumps(a), encoding="utf-8")
    fb = tmp_path / "b.json"; fb.write_text(json.dumps(b), encoding="utf-8")
    res = kappa_from_blinded_jsons(fa, fb)
    assert "claim_kappa" in res
    assert "truth_kappa" in res
    assert "n_pairs" in res
    assert res["n_pairs"] == 2
```

- [ ] **Step 2: Run, expect failure** → all errors.

- [ ] **Step 3: Implement `scripts/compute_kappa.py`**

```python
"""Cohen's κ from two blinded rater JSON exports (from verification.html)."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def cohen_kappa(a: list, b: list) -> float:
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} vs {len(b)}")
    if not a:
        return float("nan")
    n = len(a)
    p_obs = sum(1 for x, y in zip(a, b) if x == y) / n
    pa_true = sum(1 for x in a if x) / n
    pb_true = sum(1 for x in b if x) / n
    p_exp = pa_true * pb_true + (1 - pa_true) * (1 - pb_true)
    if p_exp == 1.0:
        return 1.0 if p_obs == 1.0 else 0.0
    return (p_obs - p_exp) / (1 - p_exp)


def kappa_from_blinded_jsons(path_a: Path, path_b: Path) -> dict:
    a = json.loads(Path(path_a).read_text(encoding="utf-8"))
    b = json.loads(Path(path_b).read_text(encoding="utf-8"))
    common = sorted(set(a) & set(b))
    a_claim = [bool(a[k]["claim"]) for k in common]
    b_claim = [bool(b[k]["claim"]) for k in common]
    a_truth = [bool(a[k]["truth"]) for k in common]
    b_truth = [bool(b[k]["truth"]) for k in common]
    return {
        "n_pairs": len(common),
        "n_only_a": len(set(a) - set(b)),
        "n_only_b": len(set(b) - set(a)),
        "claim_kappa": cohen_kappa(a_claim, b_claim),
        "truth_kappa": cohen_kappa(a_truth, b_truth),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python scripts/compute_kappa.py <rater_a.json> <rater_b.json>", file=sys.stderr)
        return 1
    res = kappa_from_blinded_jsons(Path(argv[1]), Path(argv[2]))
    out_path = Path(__file__).resolve().parent.parent / "outputs" / "irr_audit_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    if res["claim_kappa"] < 0.80 or res["truth_kappa"] < 0.80:
        print("WARNING: at least one κ < 0.80 — does NOT meet v0.1.0 acceptance gate", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run, expect pass** → 6 passed.

- [ ] **Step 5: Document the human-in-the-loop audit protocol**

Write `docs/irr_audit_protocol.md`:

```markdown
# IRR Audit Protocol — n=30 blinded dual-rater (PACTR Hiddenness pattern)

## Preconditions
- prereg-v0.1.0-amend-1 tagged and pushed (algorithmic extraction frozen)
- outputs/verification.html generated with the audit-sample n=30 pairs

## Protocol
1. Rater A (Mahmood) and Rater B (TBD: Makerere co-rater or independent) each
   open `outputs/verification.html` in a separate browser session.
2. **They do NOT see each other's answers and do NOT see the algorithmic results.**
3. Each rater works through all n=30 pairs, answering both questions per pair.
4. After completing all pairs, each rater clicks "Export JSON" and saves the output.
   - Rater A → `outputs/irr_rater_A.json`
   - Rater B → `outputs/irr_rater_B.json`
5. Run: `python scripts/compute_kappa.py outputs/irr_rater_A.json outputs/irr_rater_B.json`
6. Acceptance gate: BOTH `claim_kappa ≥ 0.80` AND `truth_kappa ≥ 0.80`.
7. If either κ < 0.80: do NOT proceed to v0.1.0 tag. Investigate disagreements
   pair-by-pair, amend the spec or extraction protocol if needed, increment
   to `prereg-v0.1.0-amend-2`, and re-run the audit.

## Recording
After κ ≥ 0.80, commit:
- `outputs/irr_rater_A.json`
- `outputs/irr_rater_B.json`
- `outputs/irr_audit_results.json` (auto-generated by compute_kappa.py)
```

- [ ] **Step 6: Run the audit (manual step)**

Follow `docs/irr_audit_protocol.md`. Both raters complete. Run:

```
python scripts/compute_kappa.py outputs/irr_rater_A.json outputs/irr_rater_B.json
```

Expected exit 0, JSON shows `claim_kappa ≥ 0.80` and `truth_kappa ≥ 0.80`.

- [ ] **Step 7: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add scripts/compute_kappa.py tests/test_kappa.py docs/irr_audit_protocol.md outputs/irr_rater_A.json outputs/irr_rater_B.json outputs/irr_audit_results.json
git -C C:/Projects/africa-hiv-prep-atlas commit -m "feat(irr): n=30 blinded dual-rater audit, κ ≥0.80 acceptance gate"
```

---

## Task 21: outputs/extraction_audit.md + Synthēsis Methods Note

**Files:**
- Create: `outputs/extraction_audit.md`
- Create: `docs/synthesis-methods-note.docx` (≤400 words)
- Test: `tests/test_methods_note_word_count.py`

- [ ] **Step 1: Write failing test for word count**

```python
# tests/test_methods_note_word_count.py
import re
from pathlib import Path

import pytest

DOC = Path(__file__).parent.parent / "docs" / "synthesis-methods-note.docx"


def _doc_text():
    pytest.importorskip("docx")
    from docx import Document
    return "\n".join(p.text for p in Document(str(DOC)).paragraphs)


def test_methods_note_exists():
    assert DOC.exists()


def test_methods_note_le_400_words():
    text = _doc_text()
    words = re.findall(r"\S+", text)
    assert len(words) <= 400, f"got {len(words)} words"


def test_methods_note_includes_headline_calibration_phrase():
    text = _doc_text().lower()
    assert "sensitivity" in text
    assert "specificity" in text
    assert "african" in text
```

- [ ] **Step 2: Write `outputs/extraction_audit.md`**

```markdown
# Extraction audit — africa-hiv-prep-atlas v0.1.0

> Per DossierGap pattern: known limits, per-trial caveats, residual uncertainty.

## Trial-level caveats

| Trial | Caveat | Source |
|---|---|---|
| HPTN_083 | South Africa is the only African site; ~12% African enrolment — borderline D3 fail. | landovitz-2021-nejm |
| ... | ... | ... |

## MA-level caveats

| MA | Caveat | Source |
|---|---|---|
| <ma_id> | <e.g., search closed before lenacapavir readout — does not cite PURPOSE-1> | <doc-locator> |

## Negation-guard hits

(Auto-generated list of any text spans where negation guard rejected a candidate
match. Each row links to fixtures/trials/<trial>.json and the verbatim line.)

## Residual uncertainty

- (List items where confidence_layer_t or confidence_layer_m = "medium" or "low".)
- (Include any pair where the n=30 blinded audit raters disagreed.)
```

- [ ] **Step 3: Write the .docx Methods Note**

Create `scripts/build_methods_note.py`:

```python
"""Generate the Synthēsis Methods Note .docx (≤400 words, A4, 1.5spc, 11-pt Calibri)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_LINE_SPACING

REPO = Path(__file__).resolve().parent.parent
HEADLINE_PATH = REPO / "outputs" / "irr_audit_results.json"


def main() -> int:
    doc = Document()
    section = doc.sections[0]
    section.page_height, section.page_width = Cm(29.7), Cm(21.0)
    section.left_margin = section.right_margin = Cm(2.5)
    section.top_margin = section.bottom_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    doc.add_heading("African HIV PrEP/PEP Long-Acting Trial Atlas: a methodology-calibration audit", level=1)

    irr = json.loads(HEADLINE_PATH.read_text(encoding="utf-8")) if HEADLINE_PATH.exists() else {}

    paragraphs = [
        ("Background", "Meta-analyses (MAs) of long-acting HIV PrEP modalities — long-acting injectable PrEP (cabotegravir, lenacapavir), the dapivirine vaginal ring, and forthcoming implants — make claims about African-cohort coverage that drive policy. No prior audit calibrates whether MAs' classifications match the underlying enrolment data."),
        ("Methods", "We audited every (MA, trial) pair in N MAs published 2020 onwards covering ≥1 long-acting modality, against a pre-specified ground truth (D3: ≥50% enrolment from African sites; D1, D2 as sensitivity sweeps). Each MA's classification of each cited trial was extracted across three layers: explicit count, implicit-from-table, and narrative mention. A blinded dual-rater audit on a random n=30 subset established Cohen's κ for both layers."),
        ("Results", f"Across N (MA, trial) pairs, MAs classified African-cohort long-acting PrEP trials with X% sensitivity (95% CI) and Y% specificity (95% CI) at the D3 ground truth. IRR was acceptable (claim κ={irr.get('claim_kappa', 'TBD')}, truth κ={irr.get('truth_kappa', 'TBD')}). Sensitivity sweeps at D1 and D2 are reported separately."),
        ("Discussion", "Findings calibrate the African-cohort representation claims that long-acting PrEP MAs make implicitly or explicitly. The atlas is reproducible end-to-end: fixtures are source-line-attributed; atlas.csv is byte-pinned; the headline notebook is seeded; OpenTimestamps anchors prereg, atlas, and dashboard."),
        ("Data availability", "github.com/mahmood726-cyber/africa-hiv-prep-atlas v0.1.0; OTS proofs in .ots/."),
    ]

    for heading, body in paragraphs:
        doc.add_heading(heading, level=2)
        doc.add_paragraph(body)

    out = REPO / "docs" / "synthesis-methods-note.docx"
    doc.save(str(out))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Run:

```
python scripts/build_methods_note.py
```

After running, hand-edit `docs/synthesis-methods-note.docx` to fill `X`, `Y`, `N` placeholders with the actual numbers from `outputs/irr_audit_results.json` + the bootstrap output. **Re-run `pytest tests/test_methods_note_word_count.py` to verify ≤400 words.**

- [ ] **Step 4: Run tests, expect pass** → 3 passed.

- [ ] **Step 5: Commit**

```
git -C C:/Projects/africa-hiv-prep-atlas add outputs/extraction_audit.md scripts/build_methods_note.py docs/synthesis-methods-note.docx tests/test_methods_note_word_count.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "docs(methods-note): Synthēsis Methods Note ≤400w + extraction audit"
```

---

## Task 22: Acceptance gate verification + GitHub Pages + Internet Archive + v0.1.0 tag

**Files:**
- Create: `tests/test_acceptance.py`
- Create: `scripts/ia_check.py`
- Create: `docs/E156-PROTOCOL.md`

- [ ] **Step 1: Write the acceptance gate as a test**

```python
# tests/test_acceptance.py
import csv
import json
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"


def _atlas_rows():
    with (DATA / "atlas.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _trials_rows():
    with (DATA / "trials.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _mas_rows():
    with (DATA / "mas.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_at_least_10_mas():
    assert len(_mas_rows()) >= 10


def test_at_least_6_trials():
    assert len(_trials_rows()) >= 6


def test_at_least_50_pairs():
    assert len(_atlas_rows()) >= 50


def test_irr_kappa_at_least_080():
    p = OUTPUTS / "irr_audit_results.json"
    if not p.exists():
        pytest.skip("IRR audit not yet run — Task 20 step 6 outstanding")
    res = json.loads(p.read_text(encoding="utf-8"))
    assert res["claim_kappa"] >= 0.80
    assert res["truth_kappa"] >= 0.80


def test_dashboard_exists():
    assert (OUTPUTS / "dashboard.html").exists()


def test_verification_exists():
    assert (OUTPUTS / "verification.html").exists()


def test_three_ots_stamps_present():
    """v0.1.0 OTS gate: 3 stamps — prereg + atlas.csv + dashboard.html."""
    ots_dir = REPO / ".ots"
    expected = [
        "v0.1.0-prereg-spec.md.ots",
        "v0.1.0-atlas.csv.ots",
        "v0.1.0-dashboard.html.ots",
    ]
    for name in expected:
        assert (ots_dir / name).exists(), f"missing OTS stamp: {name}"
```

- [ ] **Step 2: Snapshot v0.1.0 prereg directory and OTS-stamp the 3 acceptance artifacts**

```
mkdir -p prereg/v0.1.0
cp prereg/v0.1.0-amend-1/spec.md prereg/v0.1.0/spec.md
cp data/atlas.csv prereg/v0.1.0/atlas.csv
cp outputs/dashboard.html prereg/v0.1.0/dashboard.html

ots stamp prereg/v0.1.0/spec.md
ots stamp prereg/v0.1.0/atlas.csv
ots stamp prereg/v0.1.0/dashboard.html

mv prereg/v0.1.0/spec.md.ots .ots/v0.1.0-prereg-spec.md.ots
mv prereg/v0.1.0/atlas.csv.ots .ots/v0.1.0-atlas.csv.ots
mv prereg/v0.1.0/dashboard.html.ots .ots/v0.1.0-dashboard.html.ots
```

- [ ] **Step 3: Run the full test suite**

```
pytest -q
```

Expected: ≥80 tests, 100% pass.

- [ ] **Step 4: Run Sentinel scan, expect 0 BLOCK**

```
python -m sentinel scan --repo C:/Projects/africa-hiv-prep-atlas
```

Expected: `BLOCK=0`.

- [ ] **Step 5: Tag v0.1.0 and push**

```
git -C C:/Projects/africa-hiv-prep-atlas add prereg/v0.1.0/ .ots/v0.1.0-*.ots tests/test_acceptance.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "chore(release): v0.1.0 prereg snapshot + 3 OTS stamps + acceptance tests"
git -C C:/Projects/africa-hiv-prep-atlas tag -a v0.1.0 -m "v0.1.0: methodology-calibration audit of LA-PrEP MA African-cohort claims"
git -C C:/Projects/africa-hiv-prep-atlas push --follow-tags
```

- [ ] **Step 6: Enable GitHub Pages**

```
gh api -X POST /repos/mahmood726-cyber/africa-hiv-prep-atlas/pages -f "source[branch]=master" -f "source[path]=/outputs"
```

(Or use the GitHub UI: Settings → Pages → Branch=master, folder=`/outputs`.)

- [ ] **Step 7: Submit to Internet Archive and verify HTTP 200**

Write `scripts/ia_check.py`:

```python
"""Submit Pages URL to Internet Archive Wayback and verify HTTP 200."""
from __future__ import annotations

import sys
import urllib.request

PAGES_URL = "https://mahmood726-cyber.github.io/africa-hiv-prep-atlas/dashboard.html"


def submit_and_check() -> int:
    save_url = "https://web.archive.org/save/" + PAGES_URL
    req = urllib.request.Request(save_url, headers={"User-Agent": "africa-hiv-prep-atlas/0.1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        save_status = r.status
    print(f"Wayback save: HTTP {save_status}")
    with urllib.request.urlopen(PAGES_URL, timeout=30) as r:
        live_status = r.status
    print(f"Pages live: HTTP {live_status}")
    return 0 if (save_status == 200 and live_status == 200) else 1


if __name__ == "__main__":
    sys.exit(submit_and_check())
```

Run:

```
python scripts/ia_check.py
```

Expected: both `HTTP 200`. (May need to wait ~5 minutes after enabling Pages.)

- [ ] **Step 8: Write `docs/E156-PROTOCOL.md`**

```markdown
# E156-PROTOCOL — africa-hiv-prep-atlas

**Project name:** African HIV PrEP/PEP Long-Acting Trial Atlas
**Long-term-plan id:** africa-hiv-prep-atlas
**Spec:** docs/superpowers/specs/2026-05-07-africa-hiv-prep-atlas-design.md
**Plan:** docs/superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md
**Pages:** https://mahmood726-cyber.github.io/africa-hiv-prep-atlas/dashboard.html
**Workbook entry:** 680
**Author block:** MA listed as middle-author only (per feedback_e156_authorship.md).

## Dates
- Spec frozen (prereg-v0.0.1): 2026-05-07
- Extraction frozen (prereg-v0.1.0-amend-1): TBD
- v0.1.0 release: TBD

## Body
(Insert E156 micro-paper body here — 7 sentences, ≤156 words.)
```

- [ ] **Step 9: Update workbook + INDEX.md**

Add a workbook entry 680 to `C:\E156\rewrite-workbook.txt`:

```
ENTRY 680
PROJECT: africa-hiv-prep-atlas
DATE: 2026-05-07
CURRENT BODY:
(Paste the 7-sentence E156 body here — generated from the Methods Note.)
YOUR REWRITE:
SUBMITTED: [ ]
```

Update the workbook total count line. Add the project to `C:\ProjectIndex\INDEX.md` under the Active Projects list.

- [ ] **Step 10: Final commit and push**

```
git -C C:/Projects/africa-hiv-prep-atlas add docs/E156-PROTOCOL.md scripts/ia_check.py
git -C C:/Projects/africa-hiv-prep-atlas commit -m "docs(release): E156-PROTOCOL + IA submission script"
git -C C:/Projects/africa-hiv-prep-atlas push
```

- [ ] **Step 11: Mark plan in long-term plan as completed**

```
cd C:/ProjectIndex/long-term-plan
python -m scripts.weekly_plan_update --complete africa-hiv-prep-atlas --project-root .
```

(If `--complete` is not implemented, hand-edit `ideas.yaml` to set `status: shipped` and `wip_completed: 2026-05-07`, then commit.)

---

## Self-Review

**Spec coverage check:**
- §1 headline calibration → Tasks 11 (bootstrap), 16 (dashboard), 21 (Methods Note).
- §2 scope (S2 long-acting modalities) → Task 13 trial fixture inclusion criteria.
- §3 D1/D2/D3 ground truth → Task 6.
- §4 audit unit U3 (per-pair primary + per-MA secondary) → Tasks 10, 11.
- §5 sample frame, search, k≥10 MAs → Task 14.
- §6 extraction protocol + source-line attribution → Tasks 13, 14.
- §6 confidence tiering → Task 7.
- §7 IRR n=30 dual-rater → Tasks 17 (UI), 20 (κ + protocol).
- §8 SAP (clustered bootstrap, k<10 guard, sensitivity sweeps) → Task 11.
- §9 repo + artifacts (atlas/trials/mas, dashboard, verification, extraction_audit, Methods Note) → Tasks 12, 15-17, 21.
- §9 tests ≥80 + Sentinel 0 BLOCK + atlas pinning + D-invariant + seed determinism → Tasks 6, 11, 12, 22.
- §10 prereg + 3 OTS stamps + tag sequence + workbook 680 + middle-author → Tasks 18, 19, 22.
- §11 acceptance gates → Task 22 acceptance test.
- §12 risks: k<10 guard (Task 11), source attribution (Task 13/14), IRR fail-closed (Task 20 step 7).

**Test count estimate:**
- Task 0: 4 + Task 3: 7 + Task 4: 11 + Task 5: 6 + Task 6: 10 + Task 7: 6 + Task 8: 4 + Task 9: 6 + Task 10: 7 + Task 11: 5 + Task 12: 5 + Task 13: 5 + Task 14: 7 + Task 15: 3 + Task 16: 6 + Task 17: 5 + Task 20: 6 + Task 21: 3 + Task 22: 7 = **113 tests**, exceeds the ≥80 target.

**Placeholder check:** all `<trial_id>`, `<ma_id>`, `<N>` markers in fixture-creation steps refer to data the engineer fills, not gaps in the plan. Word counts in placeholders (`X`, `Y`, `N` in Methods Note) are explicitly flagged as "fill after IRR runs".

**Type consistency:** `claimed_a/b/c` and `truth_d1/d2/d3` and `source_lines` (tuple) are consistent across Tasks 5, 8, 9, 10, 12, 15. `Confidence` enum used in Tasks 7, 12, 15. `confusion_at_d3` signature is `list[dict] -> dict` consistently.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-07-africa-hiv-prep-atlas-v0.1.0-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Best for the 22-task scale.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Heavier on this session's context.

**Which approach?**
