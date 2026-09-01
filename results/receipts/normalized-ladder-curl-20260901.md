# Editable curl receipt — normalized ladder (2026-09-01)

Replace `BASE_URL` with the private overlay endpoint from the control plane
and `MODEL_ID` with the lane-scoped served model id. All commands were
executed verbatim from the lane head node with the fixture file present.

## 0. Fixture probe (token count check)

```bash
curl -s -m 240 -w '\nTIME_TOTAL:%{time_total}' \
  "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  --data @/tmp/dsv4-fixture-2941.json
```

Measured: `prompt_tokens=2941`, `cached_tokens=0`, `TIME_TOTAL=1.877711`
(first cold POST after freeze; this is the uncached-prefill datum).

## 1. Warm streaming TTFT (same fixture)

```bash
curl -sN -m 600 \
  "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  --data <(jq '. + {max_tokens: 1, stream: true}' /tmp/dsv4-fixture-2941.json)
```

Measured: first-token medians across 3 reps: 0.298 s (reps 0.351 / 0.298 / 0.298).

## 2. Greedy 400-token ladder request (per concurrent request)

```bash
curl -s -m 600 \
  "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  --data <(jq '. + {max_tokens: 400, temperature: 0, ignore_eos: true}' /tmp/dsv4-fixture-2941.json)
```

Measured finish reason: `length`; completion tokens exactly 400 per request.
The ladder harness issues these concurrently at C1/C2/C4/C8/C16 (warmup
followed by 3 measured reps) and records usage, walls, thermals, restarts:
`results/receipts/normalized-ladder-20260901.json`.

## 3. Correctness (vision, answer not disclosed)

```bash
RED_PNG_B64=$(python3 - <<'EOF'
import base64, struct, zlib
def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
idat = zlib.compress(b"\x00\xff\x00\x00")
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
print(base64.b64encode(png).decode())
EOF
)
curl -s -m 300 "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  --data @- <<JSON
{
  "model": "$MODEL_ID",
  "max_tokens": 200,
  "temperature": 0,
  "messages": [{"role": "user", "content": [
    {"type": "text", "text": "Describe what you observe in the image."},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,$RED_PNG_B64"}}
  ]}]
}
JSON
```

Measured: `multimodal_tokens={image: 117}`, model answered a solid uniform
red rectangle (pass; prompt never discloses the expected answer).
