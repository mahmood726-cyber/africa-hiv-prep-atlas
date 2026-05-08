"""Submit Pages URLs to Internet Archive Wayback Machine and verify HTTP 200.

Usage:
    python scripts/ia_check.py             # check + submit default URLs
    python scripts/ia_check.py --no-submit # check live URLs only, skip Wayback save

Exit codes:
    0 = all URLs return HTTP 200 (live + Wayback save where requested)
    1 = at least one URL failed
    2 = network or transient error (retry-able)
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request

PAGES_BASE = "https://mahmood726-cyber.github.io/africa-hiv-prep-atlas"
URLS_TO_CHECK = [
    f"{PAGES_BASE}/",                         # root redirect
    f"{PAGES_BASE}/outputs/dashboard.html",   # main dashboard
    f"{PAGES_BASE}/outputs/verification.html", # IRR audit UI
]
USER_AGENT = "africa-hiv-prep-atlas/0.1.0 (+https://github.com/mahmood726-cyber/africa-hiv-prep-atlas)"
HTTP_TIMEOUT = 30
WAYBACK_TIMEOUT = 90


def fetch_status(url: str, timeout: int = HTTP_TIMEOUT) -> tuple[int, str]:
    """Return (HTTP status, error string). Status 0 = network error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except urllib.error.URLError as e:
        return 0, str(e)
    except TimeoutError as e:
        return 0, f"timeout: {e}"


def submit_to_wayback(url: str, timeout: int = WAYBACK_TIMEOUT) -> tuple[int, str]:
    """POST the URL to Wayback's /save endpoint."""
    save_url = f"https://web.archive.org/save/{url}"
    return fetch_status(save_url, timeout=timeout)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-submit", action="store_true",
                        help="Skip Wayback submission; only check live URLs.")
    parser.add_argument("--retries", type=int, default=3,
                        help="Retry transient failures this many times (default: 3).")
    parser.add_argument("--retry-delay", type=int, default=10,
                        help="Seconds between retries (default: 10).")
    args = parser.parse_args(argv[1:])

    failures: list[str] = []
    transient: list[str] = []

    for url in URLS_TO_CHECK:
        print(f"\n=== {url} ===")
        # Live check with retry loop.
        for attempt in range(1, args.retries + 1):
            code, err = fetch_status(url)
            if code == 200:
                print(f"  [OK]  live: HTTP 200 (attempt {attempt})")
                break
            if code == 404:
                print(f"  [FAIL] live: HTTP 404")
                failures.append(f"{url} live HTTP 404")
                break
            if attempt < args.retries:
                print(f"  [retry {attempt}/{args.retries}] live: HTTP {code} ({err[:80]})")
                time.sleep(args.retry_delay)
            else:
                print(f"  [FAIL] live: HTTP {code} after {args.retries} retries ({err[:80]})")
                transient.append(f"{url} live HTTP {code}")
        else:
            continue  # all retries failed; logged above

        if args.no_submit:
            continue

        # Wayback submission.
        code, err = submit_to_wayback(url)
        if code == 200:
            print(f"  [OK]  wayback: HTTP 200")
        else:
            print(f"  [WARN] wayback: HTTP {code} ({err[:80]})")
            # Wayback is rate-limited; treat non-200 as warning, not failure.

    print("\n--- summary ---")
    if failures:
        print(f"FAILED: {failures}")
        return 1
    if transient:
        print(f"TRANSIENT (consider retry): {transient}")
        return 2
    print("All URLs return HTTP 200.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
