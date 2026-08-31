# Evidence log — Vision-Exp on 2x DGX Spark

Sanitized, chronological. Internal coordination receipts are omitted.
No raw logs, IPs, hostnames, or process identifiers.

## 2026-08-31 — preflight (read-only)

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
| Other shared boot-disk mount | present on node A — **policy-forbidden for weights** | absent |

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
gate fails and blocks all model actions. Owner-unblock options were
recorded internally. No transfer, mount, service, or
model action has been performed by this lane.

## Pending (gated on storage unblock)

- Single-node import/capacity gate.
- Two-node distributed ladder (TP=2, supported runtime).
- Performance + quality smoke at fixed prompts.
- Node release receipt.

## 2026-08-31 — storage correction and safety re-resolution

- **Correction:** this DGX lane is independent from the other hardware
  environment. The earlier cross-cluster canonical-export path is
  withdrawn and must not be mounted or reused. Historical TP=1
  capacity evidence is retained, but that path is not an approved
  recipe.
- The prior lane-owned D-state engine cleared naturally. Fresh bounded
  read-only probes found zero GPU compute processes and zero D-state
  processes on both nodes, stable available memory, idle/cool
  accelerators, and no OOM/Xid in the preceding hour. No remediation
  occurred.
- Both intended node-local user caches resolve to writable,
  non-rotational NVMe-backed storage with ample capacity. The pinned
  snapshot is incomplete on node A (57 files, 26 shards,
  91,467,982,585 bytes, eight partial files) and absent on node B.
  No download was started during re-resolution.
- **Checkpoint verdict: NO-GO / safety hold.** Natural process
  clearance removes one blocker but does not clear the owner hold.
  Per-node integrity proof, TP=2 startup, measurements, and publication
  remained pending at this checkpoint.

The six-phase tracked ledger is
[notebooks/dgx-experiment-ledger.ipynb](notebooks/dgx-experiment-ledger.ipynb);
machine-readable state is [results/ledger-state.json](results/ledger-state.json).

## 2026-08-31 — authenticated-download gate

- A reusable preflight now verifies Hub identity from inside the exact
  non-interactive or container execution context and emits one field only:
  `{"auth":true}` or `{"auth":false}`. Credential material, lookup details,
  and authentication errors are suppressed.
- The preflight returned `{"auth":true}` on both nodes inside the exact
  detached-container context. No credential value or lookup detail was
  emitted or committed.
- Worker staging completed through the direct interconnect: 121.3 GB at
  approximately 490 MB/s. Both node-local snapshots then passed 48/48 shard,
  broken-link, resolved-size, and pinned-index-total checks.
- No authenticated Hub resume was required after the original resumable
  download. The reusable rule remains fail-closed: do not interrupt progress,
  and resume a stalled owned download in place only after `{"auth":true}`.
- After these gates passed, the first bounded TP=2 boot attempt started with
  the pinned reference launcher. Its startup verdict and any measurements
  remain pending; no ready-state or performance claim is made yet.

## 2026-08-31 — auth-propagation verification receipt (live)

- Owner correction processed: the authenticated-download process gate and the
  subsequent owner merge decision (receipt retained in the private lane
  record). No active downloader existed on either node at verification time,
  so no owned process was interrupted and the healthy serving experiment was
  left untouched.
- Exact serving-container context re-verified online with offline mode flags
  cleared for the probe only: token file present = true and authenticated
  Hub identity probe = PASS on both nodes. Approved credential propagation is
  persistent via the approved HF home mount; any future owned download or
  resume inherits it in this same context.
- Pinned checkpoint re-verified on both nodes: 48/48 safetensor shards and
  zero incomplete blobs in the local HF hub cache. No shard growth during
  sampling; historical partials are stale leftovers from the superseded
  cache path and are not part of the verified snapshot.
- Serving containers report healthy in the exact detached context. Ledger
  updated with this receipt; merge readiness gates unchanged.
