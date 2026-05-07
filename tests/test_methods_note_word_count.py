"""
test_methods_note_word_count.py — verify synthesis-methods-note.docx constraints.

Three tests:
1. docx file exists after build.
2. Word count of body sections is <=400.
3. Required terms ("sensitivity", "specificity", "African") are present in body.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOCX = REPO / "docs" / "synthesis-methods-note.docx"
BUILD_SCRIPT = REPO / "scripts" / "build_methods_note.py"


def _get_docx_text() -> str:
    """Extract plain text from all paragraphs in the docx."""
    from docx import Document
    doc = Document(str(DOCX))
    return " ".join(p.text for p in doc.paragraphs)


def test_methods_note_docx_exists():
    """build_methods_note.py must produce docs/synthesis-methods-note.docx."""
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert result.returncode == 0, f"build failed:\n{result.stderr}"
    assert DOCX.exists(), "synthesis-methods-note.docx not found after build"


def test_methods_note_word_count_lte_400():
    """Body text of Methods Note must not exceed 400 words (Synthesis limit)."""
    # Import the module's SECTIONS dict directly to count body-only words
    sys.path.insert(0, str(REPO / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_methods_note", BUILD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    all_body = " ".join(mod.SECTIONS.values())
    wc = len(all_body.split())
    assert wc <= 400, f"Methods Note body is {wc} words; limit is 400"


def test_methods_note_required_terms():
    """Methods Note body must mention 'sensitivity', 'specificity', and 'African'."""
    sys.path.insert(0, str(REPO / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_methods_note", BUILD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    all_body = " ".join(mod.SECTIONS.values()).lower()
    for term in ("sensitivity", "specificity", "african"):
        assert term in all_body, f"Required term '{term}' not found in Methods Note body"
