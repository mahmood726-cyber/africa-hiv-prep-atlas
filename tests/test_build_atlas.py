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
