#!/usr/bin/env python3
"""Processa as 12 artes de pets: chroma key magenta -> alpha, crop bbox,
downscale BOX, quantizacao -> /public/pets/<id>.png 192x192."""
import glob
import os

import numpy as np
from PIL import Image

RAW = "/home/user/mecha-champions/assets/raw"
OUT = "/home/user/mecha-champions/packages/web/public/pets"
SIZE = 192

PETS = [
    "scrapmouse",
    "sparkbat",
    "boltpup",
    "cogturtle",
    "medivine",
    "emberfeline",
    "frostowl",
    "leechdrone",
    "runefox",
    "magmawyrm",
    "aegisjelly",
    "zenithdrake",
]

os.makedirs(OUT, exist_ok=True)


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


def quantize(rgba, ncolors=40):
    a = rgba[:, :, 3]
    rgb = rgba[:, :, :3].copy()
    if (a > 0).any():
        med = rgb[a > 0].reshape(-1, 3).mean(axis=0).astype(np.uint8)
        rgb[a == 0] = med
    q = (
        Image.fromarray(rgb, "RGB")
        .quantize(colors=ncolors, method=Image.MEDIANCUT, dither=Image.NONE)
        .convert("RGB")
    )
    out = np.dstack([np.asarray(q).astype(np.uint8), a])
    resid = bg_mask(out[:, :, :3]) & (a > 0)
    out[resid, 3] = 0
    return out


def find(pet):
    m = sorted(glob.glob(os.path.join(RAW, f"pet_{pet}_*.png")))
    if not m:
        raise SystemExit(f"nao encontrado: pet_{pet}")
    return m[-1]


done = 0
for pet in PETS:
    src = find(pet)
    rgba = to_rgba(Image.open(src))
    bb = bbox_of(rgba[:, :, 3])
    if bb is None:
        raise SystemExit(f"vazio: {pet}")
    x0, y0, x1, y1 = bb
    crop = rgba[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    side = max(cw, ch)
    pad = int(side * 0.06)
    side += pad * 2
    sq = np.zeros((side, side, 4), dtype=np.uint8)
    ox = (side - cw) // 2
    oy = (side - ch) // 2
    sq[oy : oy + ch, ox : ox + cw] = crop
    small = resize_rgba(sq, SIZE, SIZE)
    small = quantize(small)
    Image.fromarray(small, "RGBA").save(os.path.join(OUT, f"{pet}.png"), optimize=True)
    done += 1
    print(f"{pet}: {os.path.basename(src)} -> {SIZE}x{SIZE}")

print(f"pets processados: {done}")
