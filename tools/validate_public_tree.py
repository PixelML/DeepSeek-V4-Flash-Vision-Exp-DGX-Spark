#!/usr/bin/env python3
"""Fail when the tracked public tree contains private-boundary data."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Build private names from fragments so the validator does not contain the
# forbidden strings it is designed to detect.
PRIVATE_REPO = "sean" + "phan/pixel" + "ml"
PRIVATE_LABELS = ("apo" + "llo", "chi" + "mera")

RULES = {
    "private control-plane repository": re.compile(re.escape(PRIVATE_REPO), re.I),
    "private issue-comment identifier": re.compile(r"issuecomment-\d+", re.I),
    "private tracker shorthand": re.compile(r"pixelml#\d+", re.I),
    "bare issue/PR-style number": re.compile(r"(?<![A-Za-z0-9])#\d+\b"),
    "private machine label": re.compile(r"\b(?:" + "|".join(PRIVATE_LABELS) + r")(?:-[A-Za-z0-9._-]+)?\b", re.I),
    "private IPv4 address": re.compile(
        r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
        r"100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2})\b"
    ),
    "private overlay hostname": re.compile(r"\b[A-Za-z0-9.-]+\.ts\.net\b", re.I),
    "local user path": re.compile(re.escape("/Us" + "ers/") + r"|" + re.escape("/ho" + "me/") + r"[^/<\s]+/"),
    "credential assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_./+-]{8,}"
    ),
    "full GPU UUID": re.compile(r"\bGPU-[0-9a-f-]{16,}\b", re.I),
}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8")
    return [ROOT / item for item in output.split("\0") if item]


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        for name, pattern in RULES.items():
            if pattern.search(rel):
                failures.append(f"{rel}: filename violates {name}")
        text = path.read_bytes().decode("utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for name, pattern in RULES.items():
                if pattern.search(line):
                    failures.append(f"{rel}:{line_number}: {name}")

    if failures:
        print("public-boundary validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"public-boundary validation passed ({len(tracked_files())} tracked files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
