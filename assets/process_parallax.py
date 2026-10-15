#!/usr/bin/env python3
"""Fase B: processa as camadas de parallax e os props do hub.

- pl_sky: sem chroma key (camada de fundo opaca)
- pl_mountains / pl_skyline / pl_mid / pl_fg: chroma key magenta -> alpha
- pl_props: chroma key + corte da grade 3x2 -> props separados

Saida: packages/web/public/city/
"""
import glob
import os

import numpy as np
from PIL import Image

RAW = "/home/user/mecha-champions/assets/raw"
OUT = "/home/user/mecha-champions/packages/web/public/city"
os.makedirs(OUT, exist_ok=True)


def newest(prefix):
    fs = sorted(glob.glob(f"{RAW}/{prefix}_*.png"))
    if not fs:
        raise SystemExit(f"sem arte para {prefix}")
    return fs[-1]


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
    out = np.dstack([rgb.astype(np.uint8), a_s.astype(np.uint8)])
    out[:, :, 3] = np.where(out[:, :, 3] > 110, 255, 0)
    return out


def quantize_rgba(rgba, colors=40):
    a = rgba[:, :, 3]
    rgb = Image.fromarray(rgba[:, :, :3], "RGB")
    q = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    out = np.dstack([np.asarray(q), a])
    return Image.fromarray(out, "RGBA")


def save_layer(prefix, name, width, colors=40, chroma=True, crop_bottom=None):
    im = Image.open(newest(prefix))
    if chroma:
        rgba = to_rgba(im)
        bb = bbox_of(rgba[:, :, 3])
        if bb:
            x0, y0, x1, y1 = bb
            rgba = rgba[y0:y1, x0:x1]
    else:
        arr = np.asarray(im.convert("RGB")).astype(np.uint8)
        rgba = np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)])
    if crop_bottom:
        h = rgba.shape[0]
        rgba = rgba[int(h * (1 - crop_bottom)) :]
    h = max(1, round(width * rgba.shape[0] / rgba.shape[1]))
    small = resize_rgba(rgba, width, h) if chroma else None
    if small is None:
        rgbim = Image.fromarray(rgba[:, :, :3], "RGB").resize((width, h), Image.BOX)
        small = np.dstack([np.asarray(rgbim), np.full((h, width), 255, np.uint8)])
    out = quantize_rgba(small, colors)
    path = f"{OUT}/{name}.png"
    out.save(path)
    print(f"{name}: {out.size[0]}x{out.size[1]}")


PROPS = [
    ("prop_lamp", 96),
    ("prop_sign", 104),
    ("prop_crates", 84),
    ("prop_vending", 92),
    ("prop_antenna", 132),
    ("prop_trash", 68),
]


def save_props():
    im = Image.open(newest("pl_props"))
    rgba = to_rgba(im)
    H, W = rgba.shape[:2]
    ch, cw = H // 2, W // 3
    idx = 0
    for row in range(2):
        for col in range(3):
            cell = rgba[row * ch : (row + 1) * ch, col * cw : (col + 1) * cw]
            bb = bbox_of(cell[:, :, 3])
            if not bb:
                print("celula vazia", row, col)
                idx += 1
                continue
            x0, y0, x1, y1 = bb
            cut = cell[y0:y1, x0:x1]
            name, target_h = PROPS[idx]
            tw = max(1, round(target_h * cut.shape[1] / cut.shape[0]))
            small = resize_rgba(cut, tw, target_h)
            quantize_rgba(small, 28).save(f"{OUT}/{name}.png")
            print(f"{name}: {tw}x{target_h}")
            idx += 1


if __name__ == "__main__":
    save_layer("pl_sky", "pl_sky", 960, colors=44, chroma=False)
    save_layer("pl_mountains", "pl_mountains", 1280, colors=32)
    save_layer("pl_skyline", "pl_skyline", 1440, colors=40)
    save_layer("pl_mid", "pl_mid", 1440, colors=40)
    save_layer("pl_fg", "pl_fg", 1440, colors=40)
    save_props()
