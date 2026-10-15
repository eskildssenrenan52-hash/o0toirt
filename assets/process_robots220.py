#!/usr/bin/env python3
"""Processa os 100 sprite sheets novos (ids 21-120) do roster220.json.
Mesmo pipeline do process.py: chroma key magenta -> alpha, fatiar 4x4,
bbox uniao, downscale BOX, quantizacao -> strip 2048x128 + face 64x64."""
import glob
import json
import os

import numpy as np
from PIL import Image

RAW = "/home/user/mecha-champions/assets/raw"
OUT = "/home/user/mecha-champions/packages/web/public"
ROSTER = "/home/user/mecha-champions/assets/roster220.json"

os.makedirs(f"{OUT}/robots", exist_ok=True)


def find(pattern):
    m = sorted(glob.glob(os.path.join(RAW, pattern)))
    if not m:
        raise SystemExit(f"nao encontrado: {pattern}")
    return m[-1]


def bg_mask(arr):
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    return (r > 110) & (b > 110) & (g < np.minimum(r, b) * 0.62)


def to_rgba(im):
    arr = np.asarray(im.convert("RGB")).astype(np.uint8)
    a = np.where(bg_mask(arr), 0, 255).astype(np.uint8)
    return np.dstack([arr, a])


def bbox_of(alpha):
    ys, xs = np.nonzero(alpha > 8)
    if len(ys) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def resize_rgba(rgba, w, h):
    arr = rgba.astype(np.float32)
    a = arr[:, :, 3:4] / 255.0
    pre = (arr[:, :, :3] * a).clip(0, 255).astype(np.uint8)
    a8 = (a[:, :, 0] * 255).astype(np.uint8)
    pre_s = np.asarray(Image.fromarray(pre, "RGB").resize((w, h), Image.BOX)).astype(np.float32)
    a_s = np.asarray(Image.fromarray(a8, "L").resize((w, h), Image.BOX)).astype(np.float32)
    an = np.clip(a_s / 255.0, 1e-4, 1.0)[:, :, None]
    rgb = (pre_s / an).clip(0, 255)
    hard = np.where(a_s >= 108, 255, 0).astype(np.uint8)
    return np.dstack([rgb.astype(np.uint8), hard])


def quantize(rgba, ncolors=48):
    a = rgba[:, :, 3]
    rgb = rgba[:, :, :3].copy()
    if (a > 0).any():
        med = rgb[a > 0].reshape(-1, 3).mean(axis=0).astype(np.uint8)
        rgb[a == 0] = med
    q = Image.fromarray(rgb, "RGB").quantize(
        colors=ncolors, method=Image.MEDIANCUT, dither=Image.NONE
    ).convert("RGB")
    out = np.dstack([np.asarray(q).astype(np.uint8), a])
    resid = bg_mask(out[:, :, :3]) & (a > 0)
    out[resid, 3] = 0
    return out


def save(rgba, path):
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def grid_cells(rgba, cols, rows):
    h, w = rgba.shape[:2]
    cw, ch = w // cols, h // rows
    return [rgba[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            for r in range(rows) for c in range(cols)]


def fit_into(cell_rgba, box_w, box_h, out_w, out_h, anchor="bottom"):
    bb = bbox_of(cell_rgba[:, :, 3])
    if bb is None:
        return np.zeros((out_h, out_w, 4), np.uint8)
    x0, y0, x1, y1 = bb
    crop = cell_rgba[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    scale = min(box_w / cw, box_h / ch)
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(ch * scale)))
    small = resize_rgba(crop, nw, nh)
    canvas = np.zeros((out_h, out_w, 4), np.uint8)
    ox = (out_w - nw) // 2
    oy = out_h - nh if anchor == "bottom" else (out_h - nh) // 2
    canvas[oy:oy + nh, ox:ox + nw] = small
    return canvas


FRAME = 128
FRAME_BOX = (120, 122)

roster = json.load(open(ROSTER))
done = []
for n, r in enumerate(roster):
    rid = r["i"]
    num = 121 + n
    out_strip = f"{OUT}/robots/{rid}.png"
    if os.path.exists(out_strip) and os.environ.get("FORCE") != "1":
        done.append((rid, r["n"]))
        continue
    src = find(f"robot_{num:03d}_{rid}_*.png")
    rgba = to_rgba(Image.open(src))
    cells = grid_cells(rgba, 4, 4)
    boxes = [b for b in (bbox_of(c[:, :, 3]) for c in cells) if b]
    ux0 = min(b[0] for b in boxes)
    uy0 = min(b[1] for b in boxes)
    ux1 = max(b[2] for b in boxes)
    uy1 = max(b[3] for b in boxes)
    cw, chh = ux1 - ux0, uy1 - uy0
    scale = min(FRAME_BOX[0] / cw, FRAME_BOX[1] / chh)
    nw, nh = max(1, int(round(cw * scale))), max(1, int(round(chh * scale)))
    strip = np.zeros((FRAME, FRAME * 16, 4), np.uint8)
    for i, cell in enumerate(cells):
        crop = cell[uy0:uy1, ux0:ux1]
        small = resize_rgba(crop, nw, nh)
        ox = i * FRAME + (FRAME - nw) // 2
        strip[FRAME - nh:FRAME, ox:ox + nw] = small
    strip = quantize(strip, 56)
    save(strip, out_strip)
    save(fit_into(strip[:, 0:FRAME], 60, 60, 64, 64, "center"),
         f"{OUT}/robots/{rid}_face.png")
    done.append((rid, r["n"]))
    print("robot", num, rid, "ok", flush=True)

# manifest: mantem os 20 originais e acrescenta os novos
mpath = f"{OUT}/robots/manifest.json"
man = json.load(open(mpath))
existing = {x["id"] for x in man["robots"]}
for rid, name in done:
    if rid not in existing:
        man["robots"].append({"id": rid, "name": name})
json.dump(man, open(mpath, "w"), ensure_ascii=False, indent=1)
print("total robots no manifest:", len(man["robots"]))
