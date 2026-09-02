#!/usr/bin/env python3
"""Verify shard count, broken links, and total bytes against the pinned index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED_SHARDS = 48
EXPECTED_FILES = 82
EXPECTED_BYTES = 167_831_846_872


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <model-dir>", file=sys.stderr)
        return 2

    model_dir = Path(sys.argv[1])
    index_path = model_dir / "model.safetensors.index.json"
    if not index_path.is_file():
        print(f"missing index: {index_path}", file=sys.stderr)
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    total_size = index.get("metadata", {}).get("total_size")

    shards = sorted(model_dir.glob("model-*-of-*.safetensors"))
    broken = [p for p in shards if p.is_symlink() and not p.resolve().exists()]

    ok = True
    if len(shards) != EXPECTED_SHARDS:
        print(f"shard count {len(shards)} != expected {EXPECTED_SHARDS}", file=sys.stderr)
        ok = False
    if broken:
        print(f"{len(broken)} broken shard link(s): {[str(p) for p in broken]}", file=sys.stderr)
        ok = False
    if total_size != EXPECTED_BYTES:
        print(f"index total_size {total_size} != expected {EXPECTED_BYTES}", file=sys.stderr)
        ok = False

    all_files = [p for p in model_dir.rglob("*") if p.is_file()]
    if len(all_files) != EXPECTED_FILES:
        print(f"file count {len(all_files)} != expected {EXPECTED_FILES} (non-fatal)", file=sys.stderr)

    if not ok:
        return 1

    print(f"verified: {len(shards)}/{EXPECTED_SHARDS} shards, 0 broken links, {total_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
