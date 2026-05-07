"""External-prereq preflight for africa-hiv-prep-atlas v0.1.0.

Fails closed (exit 1) with a per-check action list if any of:
  (a) project path is already a git repo (lessons.md git-init safety)
  (b) Sentinel CLI not importable
  (c) AACT snapshot not resolvable (candidate-root discovery)
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
    fixed = [
        Path(os.environ.get("AACT_ROOT", "")) / "studies.txt" if os.environ.get("AACT_ROOT") else None,
        Path(r"C:\AACT\studies.txt"),
        Path(r"D:\AACT\studies.txt"),
    ]
    for c in fixed:
        if c and c.exists():
            return True, f"OK: AACT studies.txt at {c}"
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
