# DeepSeek-V4-Flash-Vision-Exp on 2x DGX Spark (GB10)

Fit/startup/performance evidence for the official
[deepseek-ai/DeepSeek-V4-Flash-Vision-Exp](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp)
checkpoint (FP8 e4m3, 48 shards, 167.83 GB) on a two-node DGX Spark
kit. Status: **MEASURED — single-node capacity gate FAILED (TP=1 cannot
fit); both node-local checkpoints and exact-context Hub authentication
PASS**. This repository
carries the sanitized public evidence trail.

## TL;DR

- **Current state: staging complete on both nodes; authentication PASS.**
  A former
  cross-cluster storage assumption is withdrawn; that path must not be
  mounted or reused.
- Single-node startup gate **measured**. Attempt 1: BLOCKED_GATE — the
  fp8_ds_mla KV layout requires an explicit fp8 kv-cache dtype (config
  assert, fixed with `--kv-cache-dtype fp8_ds_mla`). Attempt 2: passed
  architecture/import and streamed weights from the canonical export,
  then **CUDA OOM during weight load**: 115.03 GiB PyTorch-allocated of
  121.69 GiB total, 2.09 GiB free, 2.00 GiB requested.
- **Verdict: CAPACITY_FAIL — one GB10 cannot serve the 167.83 GB
  checkpoint at TP=1.** Engine exited cleanly; checkpoint untouched.
- The lane-owned stuck process cleared naturally. A fresh read-only
  check found both accelerators idle, zero GPU/D-state processes, stable
  memory, and no recent OOM/Xid. This cleared the stale-process blocker;
  checkpoint staging was subsequently authorized.
- Both node-local checkpoints are integrity-complete: 48/48 shards,
  zero broken links, and the pinned index total on each node. Worker
  staging completed through the direct interconnect; no model-load or
  GPU process was started for staging.
- Hub authentication returns `{"auth":true}` inside the exact detached
  container context on both nodes. The preflight never prints credential
  material.
- The first bounded TP=2 boot attempt is now in progress. If it reaches
  ready state, the lane proceeds to measured prefill/decode/TTFT, then
  the full completion bar: quality smoke, ClipProxy wiring, live
  verified request, independent exact-head review.

![status card](assets/status-card.png)

The tracked six-phase experiment ledger is
[notebooks/dgx-experiment-ledger.ipynb](notebooks/dgx-experiment-ledger.ipynb),
backed by [results/ledger-state.json](results/ledger-state.json). Future
GPU work is stopped by an explicit notebook guard unless ownership,
integrity, authentication, and safety gates are all clear.

## Gates (2026-08-31, read-only)

| Gate | Result | Evidence |
|---|---|---|
| Ownership | PASS (both nodes; zero foreign GPU compute processes) | prior-owner release + fresh probes |
| OOM stability | PASS; prior hold cleared after a stable observation window | kernel journal, sanitized counts only |
| Accelerators | PASS pre-run (GB10 x2, idle, 45-48 C) | nvidia-smi |
| Interconnect | PASS (RDMA/RoCE peers up on both nodes) | rdma tools |
| Node-local cache media | PASS (writable, non-rotational NVMe on both nodes) | read-only mount/media probe |
| Node-local pinned checkpoint | PASS on both nodes | offline shard/link/index integrity receipts |
| Hub authentication in execution context | PASS on both nodes | boolean-only receipt in exact detached-container context |
| Runtime | PASS (vision vLLM image on both nodes; CUDA 13) | docker images |

See [EVIDENCE.md](EVIDENCE.md) for the full sanitized preflight and
[runs/20260831T1628Z-single-node-tp1.md](runs/20260831T1628Z-single-node-tp1.md)
for the measured single-node run manifest.

## Ladder status

1. ~~Node-local checkpoint preparation~~ DONE — both nodes PASS.
   Cross-cluster storage is withdrawn.
2. ~~Single-node import/capacity gate~~ DONE — measured CAPACITY_FAIL
   at TP=1 (see run manifest).
3. Two-node distributed ladder: first bounded TP=2 startup attempt —
   **IN PROGRESS**; TTFT/decode/throughput follow only after ready state.
4. Terminal verdict + measured service publication + independent
   exact-head review — PENDING.

## Protocol

- Model pinned at revision
  `86f746b36186f0e567729a5c06a8c918caba82a9`; exact inventory
  target is 82 files / 48 shards / 167,831,846,872 repository bytes.
  Both node-local caches pass.
- Token counts from final usage objects; every material claim labeled
  measured / inferred / community-reported / untested.
- No private infrastructure identifiers, IPs, hostnames, UUIDs, or
  process IDs in this repository.
- Run `python3 tools/hf_auth_preflight.py` inside the exact background
  or container execution context before a download starts or resumes.
  Continue only when its complete output is `{"auth":true}`.
- Run `python3 tools/validate_public_tree.py` before every public push.

## License

MIT. Benchmark code and documentation only — no model weights.
