#!/usr/bin/env python3
"""Fase F: processa os assets do laboratorio (predio do hub + fundo interno)."""
import glob
import os

import numpy as np
from PIL import Image

RAW = "/home/user/mecha-champions/assets"
OUT = "/home/user/mecha-champions/packages/web/public"


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


def trimmed(rgba, w, h):
    x0, y0, x1, y1 = bbox_of(rgba[:, :, 3])
    return resize_rgba(rgba[y0:y1, x0:x1], w, h)


# 1) predio do laboratorio no hub -----------------------------------------
src = to_rgba(Image.open(find("raw_b_lab_*.png")))
b = quantize(trimmed(src, 320, 384), 56)
save(b, f"{OUT}/city/b_lab.png")
print("b_lab.png", b.shape)

# 2) fundo do interior do laboratorio -------------------------------------
bg = Image.open(find("raw_bg_lab_*.png")).convert("RGB")
bg = bg.resize((480, 816), Image.BOX).quantize(
    colors=64, method=Image.MEDIANCUT, dither=Image.NONE
).convert("RGB")
bg.save(f"{OUT}/ui/bg_lab.png", optimize=True)
print("bg_lab.png", bg.size)
