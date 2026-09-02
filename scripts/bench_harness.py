#!/usr/bin/env python3
"""Benchmark harness for DeepSeek-V4-Flash-Vision-Exp on this recipe.

Adapted from the harness that produced the receipts under
results/2026-09-02-normalized-ladder.md and the club-dgx-spark notebook
receipts this repository links to. Not imported anywhere; run it against
your own endpoint to reproduce the C1/C4 tables and TTFT numbers in this
repository's README, or point --concurrency at other values to extend the
ladder.

Usage:
    export DSV4_ENDPOINT="http://<head-address>:8198/v1"
    python3 bench_harness.py --mode ttft --reps 3
    python3 bench_harness.py --mode decode --concurrency 1 --max-tokens 400 --reps 3
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import requests

MODEL = os.environ.get("MODEL_ID", "deepseek-v4-flash-vision-exp")
PROMPT = (
    "Write a detailed technical explanation of how speculative decoding "
    "works in large language model inference, covering the draft model, "
    "verification, and acceptance rate."
)


def base_url() -> str:
    endpoint = os.environ.get("DSV4_ENDPOINT")
    if not endpoint:
        raise SystemExit("set DSV4_ENDPOINT, e.g. http://<head-address>:8198/v1")
    return endpoint.rstrip("/")


def one_decode_request(max_tokens: int) -> dict:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    t0 = time.time()
    r = requests.post(f"{base_url()}/chat/completions", json=payload, timeout=180)
    dt = time.time() - t0
    r.raise_for_status()
    body = r.json()
    completion_tokens = body["usage"]["completion_tokens"]
    return {
        "latency_s": round(dt, 3),
        "completion_tokens": completion_tokens,
        "finish_reason": body["choices"][0]["finish_reason"],
        "tok_per_s": round(completion_tokens / dt, 2),
    }


def run_decode(concurrency: int, max_tokens: int, reps: int) -> dict:
    rounds = []
    for rep in range(reps):
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(pool.map(lambda _: one_decode_request(max_tokens), range(concurrency)))
        wall_s = time.time() - t0
        total_tokens = sum(r["completion_tokens"] for r in results)
        rounds.append({
            "rep": rep,
            "wall_s": round(wall_s, 3),
            "aggregate_tok_per_s": round(total_tokens / wall_s, 2),
            "results": results,
        })
    medians = statistics.median(r["aggregate_tok_per_s"] for r in rounds)
    return {"concurrency": concurrency, "rounds": rounds, "median_aggregate_tok_per_s": medians}


def one_ttft_request() -> float:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "max_tokens": 1,
        "stream": True,
    }
    t0 = time.time()
    with requests.post(f"{base_url()}/chat/completions", json=payload, stream=True, timeout=60) as r:
        r.raise_for_status()
        for _ in r.iter_lines():
            return time.time() - t0
    raise RuntimeError("no streamed chunk received")


def run_ttft(reps: int) -> dict:
    ttfts = [round(one_ttft_request(), 4) for _ in range(reps)]
    return {"ttfts_s": ttfts, "median_ttft_s": statistics.median(ttfts)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["decode", "ttft"], required=True)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--reps", type=int, default=3)
    args = parser.parse_args()

    if args.mode == "decode":
        result = run_decode(args.concurrency, args.max_tokens, args.reps)
    else:
        result = run_ttft(args.reps)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
