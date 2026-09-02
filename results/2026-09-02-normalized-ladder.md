# Normalized C1-C16 ladder — 2026-09-02

Sanitized receipts copied from an open, unmerged pull request against this
repository. The branch's numbers are reproduced here because they are
useful and reusable evidence; the branch itself is left untouched, per this
project's rule against rewriting another branch's history.

## Result

- Uncached prefill: 2,941 tokens in 1.877711 s (**1,566.3 tok/s**); warm
  streaming TTFT median **0.323 s**.
- Aggregate decode, median of 3 repetitions with exactly 400 completion
  tokens per request:

| Concurrency | Aggregate decode tok/s |
| ---: | ---: |
| 1 | 48.71 |
| 2 | 70.98 |
| 4 | 71.50 |
| 8 | 94.93 |
| 16 | 106.79 |

- 93/93 requests, zero errors, zero restarts; text and real-image
  correctness both passed.

## Terminal routing A/B

A same-recipe routing change was tested on the same evidence:

- Control steady-state C1: **50.36 tok/s**.
- Treatment steady-state C1: **42.52 tok/s** (**-15.6%**).
- Correctness passed in both arms.
- Because the treatment regressed, the full treatment ladder was skipped;
  the recipe in this repository does not use the treatment path.

## Runtime verdicts

- vLLM TP=2: working, measured recipe (this repository's pinned config).
- SGLang two-node path: measured host-RAM out-of-memory before any GPU
  measurement; no success claim. See
  [2026-09-02-one-variable.md](2026-09-02-one-variable.md#sglang-two-node-terminal)
  for the terminal receipt.

## Why this data lives here instead of only on the source branch

The source pull request is blocked on a GitHub Support request to purge a
prohibited historical commit object that a prior rebase left reachable; that
block is procedural, not a defect in the measurements. Copying the sanitized
numbers into a mergeable branch lets this evidence ship without waiting on
that unrelated cleanup, and without touching the source branch's history.
