# Run manifest — Vision-Exp DGX Spark ladder

Filled per run once the storage gate unblocks. One manifest per GPU
action; committed alongside its sanitized receipts.

## Fields

| Field | Value (filled at run time) |
|---|---|
| run id | _ |
| gate / rung | single-node-import / 2node-startup / 2node-perf / quality-smoke |
| model revision | 86f746b36186f0e567729a5c06a8c918caba82a9 (fixed) |
| harness revision | experiment-repo Git SHA at run time (this file's commit) |
| recipe / config revision | launch-command SHA or inline command hash (see run receipt) |
| inventory check | files / shards / bytes (must equal 82 / 48 / 167831846872) |
| weight source | canonical-store-mount / staged-fast-tier (path class only) |
| nodes | 1 or 2 (roles: head/worker) |
| runtime | image + tag + digest |
| driver versions | per node |
| topology | TP / PP / other |
| context / concurrency | maxlen / seqs |
| memory before-during-after | per node, sanitized |
| thermals + power | per node, min/med/max |
| throttle/fault events | count + class only |
| TTFT warm/cold | ms |
| decode tok/s | per stream + aggregate |
| prefill tok/s | tokens/s at fixed prompt |
| success rate | completed/attempted |
| token counting | final usage object |
| start / end / duration | UTC timestamps + wall seconds |
| verdict | PASS / CAPACITY_FAIL / RUNTIME_UNSUPPORTED / INTERCONNECT_UNSUPPORTED / KERNEL_UNSUPPORTED / PRECISION_UNSUPPORTED / ABORTED_SAFETY / BLOCKED_GATE |
| failure stage | one of: inventory / import / architecture-init / weight-load / kv-alloc / graph-capture / serve-ready / request / measurement (PASS: n/a) |
| failure class | exact exception/abort class, one line (PASS: n/a) |
| abort reason | bounded-stop trigger if aborted early (PASS: n/a) |
| raw receipts | sanitized file links |

## Reproducibility protocol (filled per run)

| Field | Value (filled at run time) |
|---|---|
| text fixture | prompt ID + SHA-256 of exact prompt bytes |
| vision fixture | image ID + SHA-256 of exact image bytes |
| sampling | temperature / top_p / max_tokens / seed |
| token targets | input tokens / output tokens per request |
| repetition | attempts per measurement + aggregation rule (median of N unless stated) |
| inspected-output result | text + vision outputs human-inspected: pass/fail + one-line description |
| communication observation | interconnect path, observed bandwidth/limitation, or n/a for single-node |
| one-node vs two-node delta | measured delta + classification (or terminal reason if not runnable) |

## Verdict vocabulary

PASS / CAPACITY_FAIL / RUNTIME_UNSUPPORTED / INTERCONNECT_UNSUPPORTED /
KERNEL_UNSUPPORTED / PRECISION_UNSUPPORTED / ABORTED_SAFETY / BLOCKED_GATE
