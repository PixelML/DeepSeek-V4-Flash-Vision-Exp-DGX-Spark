#!/usr/bin/env python3
"""Return only whether the current execution context has valid Hub auth."""

from __future__ import annotations

import contextlib
import io
import json


def authenticated() -> bool:
    """Check Hub identity without exposing credential material or errors."""

    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            from huggingface_hub import HfApi

            identity = HfApi().whoami()
        return bool(identity)
    except Exception:
        return False


def main() -> int:
    """Emit the single-field public receipt and fail closed when unauthenticated."""

    auth = authenticated()
    print(json.dumps({"auth": auth}, separators=(",", ":")))
    return 0 if auth else 3


if __name__ == "__main__":
    raise SystemExit(main())
