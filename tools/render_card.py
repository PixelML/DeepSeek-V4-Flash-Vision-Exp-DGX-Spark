#!/usr/bin/env python3
"""Render the deterministic PixelML status card (1240x1550)."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 1550
BG = (13, 17, 23)
PANEL = (22, 27, 34)
LINE = (48, 54, 61)
FG = (230, 237, 243)
MUT = (139, 148, 158)
ACCENT = (255, 196, 0)
PASS = (63, 185, 80)
FAIL = (248, 81, 73)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()

f72 = font(72, True)
while d.textlength("DeepSeek-V4-Flash-Vision-Exp", font=f72) > W - 120:
    f72 = font(f72.size - 2, True)
f34 = font(34)
f30 = font(30)
f28 = font(28, True)
f26 = font(26)
f22 = font(22)

d.text((60, 50), "DeepSeek-V4-Flash-Vision-Exp", font=f72, fill=FG)
d.text((62, 145), "2x DGX Spark (GB10, 128 GiB UMA)", font=f34, fill=MUT)
d.text((62, 190), "FP8 e4m3 checkpoint - 48 shards - 167.83 GB", font=f26, fill=MUT)

# Status panel
d.rounded_rectangle((60, 260, W-60, 420), radius=18, fill=PANEL, outline=ACCENT, width=3)
d.text((90, 290), "STATUS: BLOCKED - STORAGE GATE", font=f34, fill=ACCENT)
d.text((90, 345), "All model actions held. No bytes transferred, no mounts,", font=f26, fill=MUT)
d.text((90, 382), "no loads. Four of five preflight gates PASS (read-only).", font=f26, fill=MUT)

rows = [
    ("Ownership (both nodes, zero GPU compute)", "PASS", PASS),
    ("OOM stability (burst closed, quiet ~3 h and extending)", "PASS", PASS),
    ("Accelerators (GB10 x2 idle, 45-48 C, no throttling)", "PASS", PASS),
    ("Interconnect (RDMA/RoCE direct links up)", "PASS", PASS),
    ("Fast non-root model storage (none configured)", "FAIL", FAIL),
    ("Runtime (vision vLLM image present on both nodes)", "PASS", PASS),
]
y = 470
d.text((62, y - 40), "Preflight gates - 2026-08-31 (read-only)", font=f30, fill=MUT)
for label, verdict, color in rows:
    d.rounded_rectangle((60, y, W-60, y+88), radius=14, fill=PANEL, outline=LINE, width=2)
    d.text((90, y+26), label, font=f28, fill=FG)
    bw = d.textlength(verdict, font=f28)
    d.rounded_rectangle((W-90-bw-36, y+18, W-90, y+70), radius=10, fill=color)
    d.text((W-90-bw-18, y+26), verdict, font=f28, fill=(13, 17, 23))
    y += 108

fit = [
    "Single-node fit: 167.83 GB FP8 vs 128 GiB UMA - capacity verdict expected.",
    "Two-node TP=2: 256 GiB aggregate covers the checkpoint on paper (inferred).",
    "Next GPU action when unblocked: single-node import, then 2-node ladder.",
]
y += 30
d.text((62, y), "Fit notes", font=f30, fill=MUT)
yy = y + 48
for t in fit:
    d.text((90, yy), t, font=f26, fill=FG)
    yy += 44

d.text((62, H-150), "Checkpoint pinned at revision 86f746b (82 files / 48 shards,", font=f22, fill=MUT)
d.text((62, H-115), "167,831,846,872 bytes) verified on canonical model storage.", font=f22, fill=MUT)
d.text((62, H-70), "Public benchmark evidence - internal tracking omitted", font=f22, fill=MUT)

import os
os.makedirs("assets", exist_ok=True)
img.save("assets/status-card.png", optimize=True)
print("saved assets/status-card.png", img.size)
