# Evidence log — Vision-Exp on 2x DGX Spark

Sanitized, chronological. Every entry links its tracking-issue
receipt. No raw logs, IPs, hostnames, or process identifiers.

## 2026-08-31 — preflight (read-only)

Receipts: [#70 ack](https://github.com/seanphan/pixelml/issues/70#issuecomment-5480349566) |
[#46 release](https://github.com/seanphan/pixelml/issues/46#issuecomment-5480046695) |
[storage verdict](https://github.com/seanphan/pixelml/issues/70#issuecomment-5480508581)

### Ownership

| Check | Node A | Node B |
|---|---|---|
| GPU compute processes | 0 | 0 |
| Containers running | 0 | 0 |

- Node A released by the prior workload owner with a graceful-exit
  receipt (clean exit code 0, not OOM-killed). Measured.

### Stability

| Check | Node A | Node B |
|---|---|---|
| MemAvailable | 123.4 GiB | 121.5 GiB |
| OOM events, last 30 min | 0 | 0 |
| OOM events, last 2 h | 106 (burst ended 21:12:53 local) | 0 |
| Xid/NVRM, last 30 min | 0 | 0 |
| Uptime | ~1.5 h (recent reboot, matches owner receipt) | ~2 days |

- The node-A OOM burst is fully bounded in the journal window; the
  last fault line is identical to the one in the release receipt,
  proving the quiet window has extended ~3 h with zero recurrence.
  Measured.

### Accelerators

| Check | Node A | Node B |
|---|---|---|
| GPU | GB10, driver 580.x | GB10, driver 580.x |
| Util / power / temp | 0% / ~5 W / 48 C | 0% / ~4.4 W / 45 C |
| Throttle flags | none active | none active |

- Driver minor versions differ between nodes (580.173 vs 580.159) —
  noted for the two-node runtime gate. Measured.

### Interconnect

| Check | Node A | Node B |
|---|---|---|
| RDMA devices | 4 RoCE instances | 4 RoCE instances |
| High-speed link | up (direct peers on both direct-attach ports) | up (same) |

- Bidirectional bounded probes passed; consistent with the earlier
  two-node preflight. Measured.

### Storage

| Check | Node A | Node B |
|---|---|---|
| central library path present | no | no |
| Fast writable non-root path | none configured | none configured |
| Root NVMe | 3.7 TB vol, ~1.6 TB free — **forbidden for weights** | same |
| Shared WIP mount | present on node A — **policy-forbidden VM boot disk** | absent |

- Canonical checkpoint verified present on the central model store at
  the pinned revision: exact CMP-verified inventory (82 files / 48
  shards / 167,831,846,872 bytes), rotational HDD tier, ~7.7 TB free,
  NFS export live, both nodes inside the existing allowlist. No target
  currently mounts it; creating the mount needs owner authorization.
  Measured.

### Runtime

| Check | Node A | Node B |
|---|---|---|
| vision runtime image | present | present |
| Docker | 29.2.x | 29.2.x |
| Host CUDA / Python | 13.0 / 3.12 | 13.0 / 3.12 |
| Host torchrun | absent (container path viable) | absent |

### Verdict

**BLOCKED_STORAGE.** Four of five preflight gates pass; the storage
gate fails and blocks all model actions. Three owner-unblock options
are posted on the tracking issue. No transfer, mount, service, or
model action has been performed by this lane.

## Pending (gated on storage unblock)

- Single-node import/capacity gate.
- Two-node distributed ladder (TP=2, supported runtime).
- Performance + quality smoke at fixed prompts.
- Node release receipt.
