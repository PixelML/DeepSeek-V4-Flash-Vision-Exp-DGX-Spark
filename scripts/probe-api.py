#!/usr/bin/env python3
"""List served models without placing any credential in process arguments."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    secret_file = Path(os.environ.get("DSV4_SECRET_FILE", root / ".dsv4-api-key"))
    port = os.environ.get("API_PORT", "8198")
    headers = {}
    if secret_file.is_file():
        bearer_token = secret_file.read_text(encoding="utf-8").strip()
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/models",
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        print(json.dumps(json.load(response), separators=(",", ":")))


if __name__ == "__main__":
    main()
