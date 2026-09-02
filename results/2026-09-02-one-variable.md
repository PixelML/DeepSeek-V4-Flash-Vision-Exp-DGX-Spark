# One-variable results — 2026-09-02

Two-node DGX Spark pair, TP=2, DSpark speculative decoding at k=6 (the only
value the checkpoint's `num_nextn_predict_layers=3` allows; see
[2026-09-02-k-sweep.md](2026-09-02-k-sweep.md)).

Baseline: `nvfp4_ds_mla` KV cache, `MAX_NUM_SEQS=6`,
`MAX_NUM_BATCHED_TOKENS=8192`, CUDA graphs in `FULL_AND_PIECEWISE` mode.
Protocol for every config: a 30-prompt golden corpus for correctness, three
warm TTFT reads, three greedy 400-token runs at concurrency 1, three at
concurrency 4, GPU power sampled once a second on both nodes.

## Results

| Config | Correctness | C1 median tok/s | C4 median tok/s | TTFT | Acceptance | Outcome |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Baseline | 29/30 | 32.75 | 68.77 | 0.39 s | 21.8% | kept |
| CUDA graph mode check | n/a | n/a | n/a | n/a | n/a | already optimal, no restart needed |
| Batch-size sweep (`MAX_NUM_SEQS=16`, batch 16384) | 27/30 | 32.24 | 68.96 | 0.39 s | 21.8% | reverted |
| KV cache dtype `fp8_ds_mla` | 28/30 | 31.30 | 70.36 | 0.40 s | 19.9% | reverted |

Baseline won. Neither the batch-size sweep nor the fp8 KV cache change
cleared the bar set going in: correctness has to hold, and the
single-stream (C1) number has to actually improve, not just the four-way
(C4) aggregate. Both changes nudged C4 up by a percent or two while making
C1 worse, which is a bad trade for a service where most real traffic is a
single conversation, not four running at once.

Disabling the speculative decoder entirely was not tested — the deployment
script has no flag for it, and hand-editing the part of the config that
builds the launch command was not worth the risk on a shared node mid-lease.

Mean combined GPU power (head + worker) during the baseline benchmark
window: 68.5 W (head 30.41 W, worker 38.09 W). At the KV-dtype variant it
rose slightly to 71.27 W (head 32.18 W, worker 39.09 W) alongside its
throughput loss, so that variant is worse on both axes.

## Cross-platform data point

For a rough model-versus-platform comparison, an existing benchmark for the
text-only `DeepSeek-V4-Flash-0731` checkpoint on the same hardware was
reused rather than re-run this session — treat it as a data point, not an
apples-to-apples measurement. At short prompts and single concurrency it hit
around 75 tok/s, well above the Vision-Exp number. Some of that gap is
DSpark's own overhead (only about one in five draft tokens gets accepted
right now), and some is Vision-Exp doing more work per token. Separating
those two effects cleanly needs a matched-protocol run, which is on the list
for next time.

## SGLang two-node terminal

A two-node SGLang retry was on the table, aimed at a checkpoint-loading
approach that streams shards to the GPU instead of buffering the whole
checkpoint in host RAM first (a prior attempt died in an out-of-memory crash
before it reached a GPU measurement).

- Checkpoint size on disk (node-local HF cache): 157 GiB.
- Free RAM after stopping the resident service: 109-110 GiB available on
  each node; both nodes already had non-trivial swap in use, one of this
  lease's own stop conditions.
- Fail-closed peak-RAM estimate (bounded by checkpoint size, since no
  runtime instrumentation confirms a lower true working set): 157 GiB per
  node, which exceeds free RAM on either node. **Preflight refuses; no
  container is launched.**
- A source read of the pinned SGLang image found three weight-loading
  iterators already used by default, all tensor-streaming from mmap'd
  safetensors files rather than materializing the full checkpoint at once,
  and a default streaming dequantization path for the relevant weight/scale
  pairs. No `load_format`, environment variable, or CLI flag was found that
  bounds the per-node host-RAM working set below what those default
  streaming iterators already provide, because the buffered multi-thread
  iterator prefetches an unknown number of in-flight shards and nothing in
  the image reports or caps that buffer.

**Verdict:** no qualifying flag exists on this image. The item is stopped
here with this terminal receipt — no repeat of the identical
out-of-memory run. A future attempt would need to instrument the loader's
prefetch depth directly (a peak-RSS logger around the loader call) before
trying again; that is the only path found by this pass that plausibly
bounds host RAM below full-checkpoint size, and it is unverified rather than
absent.

The service was returned to the baseline config, confirmed healthy, and
answering both text and image requests normally throughout this session.
