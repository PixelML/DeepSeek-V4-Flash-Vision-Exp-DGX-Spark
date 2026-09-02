# Troubleshooting

## Startup hangs with an empty `--node-rank` or a ZMQ bind failure

**Symptom:** a node started by hand (outside `scripts/start-cluster.sh`) hangs at startup, or the container log shows a ZMQ bind error instead of a ready message.

**Cause:** the two-node launcher passes `NODE_RANK` and `HEADLESS` per node, and the worker must reach ready state before the head initializes distributed setup. Running `docker compose` directly, without those variables, or starting the head first, leaves one side with no rank or with nothing to bind to.

**Fix:** always start the worker first, with `NODE_RANK=1 HEADLESS=1`, then start the head. Use `scripts/start-cluster.sh`, which enforces this order; do not invoke `docker compose` on either node by hand unless you pass the same two variables explicitly.

## Single-node (TP=1) startup fails with CUDA out-of-memory

**Symptom:** the engine loads weights, then fails with a CUDA OOM error citing roughly 115 GiB already allocated on a ~121.69 GiB device.

**Cause:** the 167.83 GB FP8 checkpoint does not fit on one GB10. This is measured, not a configuration bug; see [runs/20260831T1628Z-single-node-tp1.md](../runs/20260831T1628Z-single-node-tp1.md).

**Fix:** there is no single-node fix. Use the two-node TP=2 recipe in this repository.

## SGLang two-node attempt: host out-of-memory before any GPU work starts

**Symptom:** an SGLang-based two-node attempt runs out of host RAM while dequantizing FP8 weights, before a GPU measurement is possible.

**Cause:** the checkpoint is 157 GiB on disk; a preflight estimate of peak host RAM (bounded by checkpoint size, since no runtime instrumentation confirms a lower true working set) exceeds free RAM on both nodes (109-110 GiB) before decompression even starts.

**Fix:** none confirmed on the pinned SGLang image. A source read found existing tensor-streaming iterators in the weight loader, but no flag that caps peak host RAM below full checkpoint size. This path is a measured terminal result, not a retry target — see the SGLang section in [results/2026-09-02-one-variable.md](../results/2026-09-02-one-variable.md#sglang-two-node-terminal). Use the vLLM TP=2 recipe in this repository instead.

## A very long prompt never starts generating

**Symptom:** a request with a very long prompt (hundreds of thousands of tokens) shows zero engine activity for several minutes and never returns a first token.

**Cause:** measured stall on a 380K-token chat prompt, over six minutes with no engine activity, well short of the 1,048,576-token context ceiling. The largest prefill verified end-to-end on this recipe is 29,501 tokens.

**Fix:** keep prompts at or below the verified range until a longer prompt is separately measured. If you need a longer-context data point, treat it as an open item, not an assumption that the full 1M context serves at the same latency profile as shorter prompts.

## `MTP_NUM_TOKENS` other than 6 is rejected at startup

**Symptom:** setting the draft-depth environment variable to 3 or 5 fails at container-entrypoint validation with an error naming `MTP_NUM_TOKENS`, before `vllm serve` runs.

**Cause:** the Vision-Exp checkpoint sets `num_nextn_predict_layers=3`, which the runtime enforces as a hard floor: k must be at least 5 and divisible by 3. In the range near the default, only 6 satisfies both constraints.

**Fix:** use k=6. This is a checkpoint-level constraint, not a tuning parameter for this model.

## Reboot and OOM watch

Before a fresh boot attempt, check both nodes for recent OOM events and confirm accelerators are idle and cool:

```bash
dmesg -T | grep -i -E 'oom|xid' | tail -20
nvidia-smi --query-gpu=utilization.gpu,power.draw,temperature.gpu --format=csv
```

A node that recently released a workload can show a burst of historical OOM lines from that prior process. Confirm the burst is bounded (no new lines in the last 30 minutes) before treating the node as clear, rather than assuming a single quiet check is enough.
