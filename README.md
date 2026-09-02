# DeepSeek-V4-Flash-Vision-Exp on 2x DGX Spark (GB10)

**Two DGX Spark nodes serve `deepseek-ai/DeepSeek-V4-Flash-Vision-Exp` at TP=2, 1M-token context, with DSpark speculative decoding — 36.9 output tok/s at concurrency 1 and 0.239 s TTFT, after a single GB10 could not fit the checkpoint at TP=1.**

This repository is the sanitized, reproducible evidence trail for that recipe: fit gates, startup gates, measured throughput, a k-value ablation, and two rejected one-variable changes.

## Verified configuration

| Component | Pin |
| --- | --- |
| Model | [`deepseek-ai/DeepSeek-V4-Flash-Vision-Exp`](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp) |
| Model revision | `86f746b36186f0e567729a5c06a8c918caba82a9` |
| Checkpoint | FP8 e4m3, 48 safetensor shards, 167,831,846,872 bytes |
| Served model id | `deepseek-v4-flash-vision-exp` |
| Runtime image | `ghcr.io/anemll/dspark-vllm-gx10:0.1.1@sha256:a83948492cf13df455170fb42885f5ef4db54fefe0feff0f841ecbff464ac9d8` |
| vLLM version | `0.25.2.dev0+g752a3a504` on the Anemll 0.1.1 DSpark runtime |
| Topology | 2 nodes, TP=2, one GB10 GPU per node |
| Context | 1,048,576 tokens (1M) |
| KV cache dtype | `nvfp4_ds_mla` |
| Speculative decoding | DSpark MTP, `MTP_NUM_TOKENS` (k) = 6 |
| Batch | `MAX_NUM_SEQS=6`, `MAX_NUM_BATCHED_TOKENS=8192` |
| CUDA graphs | `FULL_AND_PIECEWISE`, `VLLM_USE_BREAKABLE_CUDAGRAPH=0` |
| Launch order | worker (`NODE_RANK=1 HEADLESS=1`) starts first, then head |

The checkpoint's `num_nextn_predict_layers=3` sets a hard runtime floor on the draft depth: k must be at least 5 and divisible by 3. In that range, 6 is the only value below 9, so this recipe has one valid k, not a tuned choice among several. See [Limitations](#limitations).

A single GB10 cannot serve this checkpoint. The measured single-node (TP=1) attempt failed with a CUDA out-of-memory error after 115.03 GiB of PyTorch allocation on a 121.69 GiB device; see [runs/20260831T1628Z-single-node-tp1.md](runs/20260831T1628Z-single-node-tp1.md). Two nodes at TP=2 is the minimum working topology.

## Measured performance

### Canonical service numbers

Measured on the merged TP=2 service, live end-to-end request path, final `usage` object for every token count:

| Metric | Value |
| --- | --- |
| Uncached prefill (client-observed) | 1,789 tok/s |
| Uncached prefill (engine peak) | 36,114.9 tok/s |
| Decode, concurrency 1 | 36.9 tok/s |
| Decode, concurrency 6 (aggregate) | 112.7 tok/s (17.7-21.1 tok/s per request, `cached_tokens=0`) |
| TTFT | 0.239 s |
| Vision smoke | PASS (117 multimodal tokens) |

### Today's baseline, with power (2026-09-02)

Frozen recipe above, 30-prompt golden correctness corpus, 3 warm TTFT reads, 3 greedy 400-token runs each at concurrency 1 and 4, GPU power sampled at 1 Hz on both nodes:

| Concurrency | Median tok/s | TTFT | Correctness | Mean combined power | tok/Wh |
| --- | ---: | ---: | --- | ---: | ---: |
| 1 | 32.75 | 0.39 s | 29/30 | 68.5 W (head 30.41 W + worker 38.09 W) | 1,721 |
| 4 (aggregate) | 68.77 | 0.39 s | 29/30 | 68.5 W (head 30.41 W + worker 38.09 W) | 3,615 |

Power is the mean draw across the full benchmark window on both nodes together (idle gaps between reps included), not an isolated per-request figure. Draft-token acceptance at this baseline was 21.8%.

### Normalized C1-C16 ladder (open, unmerged evidence)

A same-recipe, wider concurrency sweep exists on an open pull request that is blocked on a GitHub history-purge request, not on the numbers. This repository copies its sanitized receipts; the branch itself is left untouched.

| Concurrency | Aggregate decode tok/s |
| ---: | ---: |
| 1 | 48.71 |
| 2 | 70.98 |
| 4 | 71.50 |
| 8 | 94.93 |
| 16 | 106.79 |

Uncached prefill on that same run: 2,941 tokens in 1.877711 s (1,566.3 tok/s); warm streaming TTFT median 0.323 s. 93/93 requests completed with zero errors and zero restarts; text and real-image correctness both passed. The gap between this ladder and the baseline table above reflects different sampling windows on the same recipe, not a configuration change — treat both as measured, not as a single canonical number.

### DSpark draft-depth (k) sweep

| k | Result |
| --- | --- |
| 3 | Rejected by the runtime validator before serving started: `Vision-Exp requires MTP_NUM_TOKENS >= 5 and divisible by 3; got 3` |
| 5 | Rejected the same way: `... got 5` |
| 6 | The only value that passes; this is the recipe's pin |

Both rejections happen at container-entrypoint validation, before any weight load or GPU time. Restoring k=6 after the rejected attempts reran the golden corpus at 29/30 keyword-match (versus 27/30 on first boot) with an unchanged, byte-identical config — consistent with vLLM's known greedy-decode batch-composition non-determinism, not a regression. Full method: [results/2026-09-02-k-sweep.md](results/2026-09-02-k-sweep.md).

### One-variable results (both reverted)

| Change | Correctness | C1 median tok/s | C4 median tok/s | Verdict |
| --- | --- | ---: | ---: | --- |
| Baseline (`MAX_NUM_SEQS=6`, batch 8192, `nvfp4_ds_mla`) | 29/30 | 32.75 | 68.77 | kept |
| `MAX_NUM_SEQS=16`, batch 16384 | 27/30 | 32.24 (-1.6%) | 68.96 (+0.3%) | reverted |
| `--kv-cache-dtype fp8_ds_mla` | 28/30 | 31.30 (-4.4%) | 70.36 (+2.3%) | reverted |

Neither change cleared the bar set going in: correctness holding at parity and single-stream (C1) throughput actually improving, not just the four-way aggregate moving. Both changes traded a small C4 gain for a worse C1 number, which is the wrong trade for a service where most real traffic is one conversation at a time. Full method: [results/2026-09-02-one-variable.md](results/2026-09-02-one-variable.md).

### Cross-platform line

A same-hardware, different-protocol benchmark for the text-only `DeepSeek-V4-Flash-0731` checkpoint already existed on the same two-node pair (concurrency-1, short prompt): 75.42 tok/s, TTFT 0.626 s. That is roughly double this recipe's Vision-Exp C1 number. Some of the gap is DSpark's own draft-acceptance overhead (about 1 in 5 draft tokens accepted at k=6), and some is Vision-Exp doing more work per token; the two effects are not separated because the protocols differ. Treat this as a directional data point, not a matched-protocol comparison. See the [club-dgx-spark notebook results](https://github.com/PixelML/club-dgx-spark/tree/main/results/2026-09-02-deepseek-v4-flash-vision-exp-2node-tp2-vllm) for a fresh, independently-run C1/TTFT check and a live text+vision "try it" demo against this same recipe.

## Reproduce

1. Two DGX Spark nodes on the same NVIDIA system-software release, with a direct RoCE link between them and enough node-local NVMe for the 156 GiB checkpoint plus caches on each node.
2. Copy the config template on the head node, fill in your topology, then copy the same file to the worker:

   ```bash
   cp .env.example .env
   $EDITOR .env
   scp .env worker:/opt/dsv4-vision-dgx-spark/.env
   ```

3. Pull the pinned runtime image on both nodes:

   ```bash
   docker pull ghcr.io/anemll/dspark-vllm-gx10:0.1.1@sha256:a83948492cf13df455170fb42885f5ef4db54fefe0feff0f841ecbff464ac9d8
   ```

4. Stage the checkpoint on both nodes at revision `86f746b36186f0e567729a5c06a8c918caba82a9` and verify 48/48 shards before serving:

   ```bash
   ./scripts/prepare-model.sh
   ```

5. Start the worker before the head, then run a smoke check:

   ```bash
   ./scripts/start-cluster.sh
   ./scripts/probe-api.py
   ```

The head node then serves an OpenAI-compatible API at `http://<head-address>:<API_PORT>/v1`. Keep it off the public internet unless it sits behind an authenticated TLS proxy; see [docs/API.md](docs/API.md).

## Limitations

- **TP=1 cannot fit the checkpoint.** Measured CUDA OOM at 115.03 GiB of 121.69 GiB device memory; see [runs/20260831T1628Z-single-node-tp1.md](runs/20260831T1628Z-single-node-tp1.md). Two nodes at TP=2 is the floor, not a choice.
- **SGLang two-node path ends in a host-RAM terminal, not a success.** A preflight estimate of peak host RAM (bounded by checkpoint size, 157 GiB) exceeded free RAM on both nodes (109-110 GiB) before any container launched. A source read of the pinned SGLang image found existing tensor-streaming loaders but no flag that bounds working set below full checkpoint size. This item is stopped with a terminal receipt, not a retry; see [results/2026-09-02-one-variable.md](results/2026-09-02-one-variable.md#sglang-two-node-terminal).
- **k=3 and k=5 are runtime-rejected, not tuning outcomes.** The checkpoint's `num_nextn_predict_layers=3` requires k >= 5 and divisible by 3; only k=6 is reachable near the default. See the k-sweep above.
- **A same-recipe routing A/B on the open, unmerged ladder came back negative.** Treatment steady-state C1 measured 42.52 tok/s against a 50.36 tok/s control, a 15.6% regression; both arms passed correctness, and the full treatment ladder was skipped once the steady-state number regressed. This did not change the pinned recipe.
- **Very long prompts stall before the engine, not inside it.** A 380K-token chat prompt produced zero engine activity for over six minutes and was abandoned; the largest prefill verified end-to-end is 29,501 tokens, well under the 1M-token context ceiling.
- **Cross-platform and cross-protocol numbers in this README are directional, not matched-protocol.** See the callouts above each one.

## Repository layout

- `patches/` - the DSpark runtime hotfixes this recipe enables, and why.
- `scripts/` - start/stop/status/prepare/probe scripts with placeholders in place of any private host or path, plus the benchmark harness.
- `results/` - dated, sanitized markdown and JSON receipts for every measurement in this README.
- `docs/API.md` - OpenAI-compatible usage, including an image `data:` URL example.
- `docs/TROUBLESHOOTING.md` - known failure signatures and fixes.
- `runs/`, `EVIDENCE.md`, `RUN-MANIFEST.md`, `notebooks/`, `tools/` - the existing fit/startup evidence ledger this README summarizes.

## License

MIT. Benchmark code and documentation only - no model weights. The checkpoint is governed by its own license on the [upstream model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp).
