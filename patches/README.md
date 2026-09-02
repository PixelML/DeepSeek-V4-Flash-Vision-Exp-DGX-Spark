# Patches

This recipe runs on the third-party Anemll DSpark vLLM runtime
(`ghcr.io/anemll/dspark-vllm-gx10:0.1.1`), which already ships most GB10/SM121
compatibility work as build-time hotfixes gated by environment flags. This
repository does not vendor that runtime's source; it pins the exact image
digest in the [README](../README.md#verified-configuration) and records which
of its hotfix gates this recipe enables and why.

## Enabled at the pinned configuration

| Flag | Purpose |
| --- | --- |
| `DSPARK_ENABLE_ISSUE141_SPARSE_MLA_CHUNK` | Long-context decode correction for the sparse MLA path used by `nvfp4_ds_mla`. Required at this recipe's context length; without it, decode correctness degrades on long sequences. |
| `DSPARK_ENABLE_ISSUE138_RESPONSES_HISTORY_COMPAT` | Compatibility shim for multi-turn request history under the OpenAI-compatible endpoint. Required for the multi-turn requests used in this recipe's correctness corpus. |
| `ENABLE_VLLM_GB10_PATCH` | The runtime's general GB10/SM121 kernel-selection patch set. Required on GB10; without it the image falls back to kernel paths that do not compile for this shape. |

## Not applicable to this recipe

The runtime image also ships hotfixes for scenarios this recipe does not hit at
the pinned configuration: dense-prefill indexer edge cases, FlashMLA workspace
sizing at prompt lengths this recipe has not exercised, grammar-constrained
decoding, and tool-call truncation. These stay at the image's defaults; if a
future run in this repository exercises one of those paths, record the flag
and the receipt here rather than silently enabling it.

## Vision support

Image input support (`hotfix-dsv4-vision-exp` in the upstream runtime) is a
startup hotfix on top of the base runtime, not a separate build: it wires the
ViT and aligner weights already present in the Vision-Exp checkpoint into the
serving path. It is active by default in the pinned image tag used by this
recipe; the [image request example](../docs/API.md#image-request) exercises
it end to end.

## Local changes in this repository

None. Every fix listed above lives in the pinned upstream image; this
repository only pins the digest and records which gates are on. If this lane
ever needs a change the upstream image does not carry, add it here as a
unified diff against the image's extracted source, following the pattern in
`scripts/prepare-model.sh` for how the extraction step would run.
