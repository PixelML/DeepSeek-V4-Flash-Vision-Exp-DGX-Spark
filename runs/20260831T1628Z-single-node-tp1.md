# Run manifest - single-node TP=1 startup gate (2026-08-31)

Filled per the schema in RUN-MANIFEST.md. One manifest per GPU action;
sanitized (no hosts, IPs, UUIDs, PIDs).

## Fields

| Field | Value (filled at run time) |
|---|---|
| run id | 20260831T1628Z-single-node-tp1 |
| gate / rung | single-node-import |
| model revision | 86f746b36186f0e567729a5c06a8c918caba82a9 (fixed) |
| harness revision | evidence-repo commit containing this file (PR head history) |
| recipe / config revision | vLLM CLI command pinned verbatim below |
| inventory check | 48/48 shards verified read-only on canonical export; file-byte total 167831846872 (verified integrity pass) |
| weight source | historical cross-cluster read-only source; owner later withdrew this path, so it must not be reused or treated as the DGX recipe |
| nodes | 1 |
| runtime | dsv4-vision-vllm:0.1.1 - vLLM 0.25.2.dev0+g752a3a504.d20260714, image sha256:ef264228... (created 2026-08-23) |
| driver versions | GB10 platform driver (current boot); exact revision in owner-side node inventory |
| topology | TP=1, PP=1 |
| context / concurrency | max_model_len 4096 / n/a (startup gate) |
| memory before-during-after | before: GPU idle; during: 115.03 GiB PyTorch-allocated of 121.69 GiB total, 2.09 GiB free at failure; after: process exited, GPU released |
| thermals + power | idle-class throughout (gate never reached steady serving); not the failure factor |
| throttle/fault events | 0 (engine exited cleanly via normal error handling) |
| TTFT warm/cold | n/a (startup gate) |
| decode tok/s | n/a (startup gate) |
| prefill tok/s | n/a (startup gate) |
| success rate | 0/2 startup attempts |
| token counting | final usage object - n/a (startup gate) |
| start / end / duration | attempt 1: 16:19Z (<1 min); attempt 2: 16:28Z-16:47Z (~19 min incl. NFS weight streaming) |
| verdict | CAPACITY_FAIL (attempt 2, measured); attempt 1 = BLOCKED_GATE (config, fixed) |
| failure stage | attempt 1: architecture-init (kv-cache dtype assert); attempt 2: weight-load |
| failure class | attempt 1: AssertionError fp8_ds_mla vs auto; attempt 2: CUDA out of memory - torch tried to allocate 2.00 GiB; device total 121.69 GiB; 115.03 GiB already PyTorch-allocated; 2.09 GiB free |
| abort reason | n/a (engine failed on its own, bounded, exited cleanly) |
| raw receipts | sanitized engine-log excerpts in this file; internal coordination receipts intentionally omitted |

## Reproducibility protocol (filled per run)

| Field | Value (filled at run time) |
|---|---|
| text fixture | n/a (startup gate) |
| vision fixture | n/a (startup gate) |
| sampling | n/a (startup gate) |
| token targets | n/a (startup gate) |
| repetition | 2 bounded attempts total, then stop (no-thrash rule) |
| inspected-output result | n/a (startup gate) |
| communication observation | n/a single-node; historical cross-cluster read-only streaming path is withdrawn and retained only to classify this completed capacity result |
| one-node vs two-node delta | TP=1 terminal: CAPACITY_FAIL measured. Two-node ladder deferred behind the owner safety hold on this lane |

## Sanitized engine-log excerpts (decisive lines)

Attempt 1 (config gate, fixed by explicit dtype):

~~~text
AssertionError: DeepseekV4 fp8_ds_mla layout only supports fp8 kv-cache, got auto
~~~

Attempt 2 (measured capacity):

~~~text
ERROR [gpu_model_runner.py] Failed to load model - not enough GPU memory.
  (original error: CUDA out of memory. Tried to allocate 2.00 GiB.
   GPU 0 has a total capacity of 121.69 GiB of which 2.09 GiB is free.
   Including non-PyTorch memory, this process has 115.29 GiB memory in use.
   Of the allocated memory 115.03 GiB is allocated by PyTorch ...)
ERROR [core.py] EngineCore failed to start.
~~~

## Launch command (attempt 2, verbatim, path class only)

~~~text
vllm serve <canonical-checkpoint-path> \
  --served-model-name dsv4-vision --port 8198 \
  --tensor-parallel-size 1 --max-model-len 4096 \
  --gpu-memory-utilization 0.92 --enforce-eager \
  --no-enable-prefix-caching --kv-cache-dtype fp8_ds_mla
~~~
