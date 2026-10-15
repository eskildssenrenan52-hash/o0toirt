#!/usr/bin/env python3
"""Fase G3: processa 5 folhas novas de VFX (grade 4x4 -> 20 tiras de 4 frames)
e consolida TODOS os fundos de arena em um unico spritesheet vertical por arena.

VFX: chroma key magenta -> alpha, escala relativa preservada dentro da linha
(frame 1 pequeno -> frame 3 no pico), tira horizontal 4x96x96 igual aos 8 antigos.

Arenas: cada fundo vira {nome}_sheet.png = 480 x (272*4), 4 frames empilhados.
"""
import glob
import os

import numpy as np
from PIL import Image

SRC = "/home/user/tmpwork/g3"
OUT = "/home/user/mecha-champions/packages/web/public"
os.makedirs(f"{OUT}/vfx", exist_ok=True)
os.makedirs(f"{OUT}/arenas", exist_ok=True)


def bg_mask(arr):
    """Chroma key estrito: so o magenta puro #FF00FF do fundo.
    Estrito de proposito para nao comer roxos/violetas dos efeitos."""
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    return (r > 180) & (b > 180) & (g < 95) & (np.abs(r - b) < 70)


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
    pre_s = np.asarray(
        Image.fromarray(pre, "RGB").resize((w, h), Image.BOX)
    ).astype(np.float32)
    a_s = np.asarray(
        Image.fromarray(a8, "L").resize((w, h), Image.BOX)
    ).astype(np.float32)
    an = np.clip(a_s / 255.0, 1e-4, 1.0)[:, :, None]
    rgb = (pre_s / an).clip(0, 255)
    hard = np.where(a_s >= 108, 255, 0).astype(np.uint8)
    return np.dstack([rgb.astype(np.uint8), hard])


def quantize(rgba, ncolors=28):
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


# --------------------------------------------------------------------- VFX
SHEETS = {
    "vfx_sheet_c": ["frost", "toxic", "cyclone", "quake"],
    "vfx_sheet_d": ["torrent", "prism", "plasma", "clang"],
    "vfx_sheet_e": ["bloom", "cosmos", "sonic", "chrono"],
    "vfx_sheet_f": ["siphon", "ward", "laser", "meteor"],
    "vfx_sheet_g": ["inferno", "shockwave", "buffup", "curse"],
}

CELL = 96
BOX = 92

made = []
for stem, names in SHEETS.items():
    path = f"{SRC}/{stem}.png"
    rgba = to_rgba(Image.open(path))
    h, w = rgba.shape[:2]
    cw, ch = w // 4, h // 4
    for row, name in enumerate(names):
        cells = []
        for col in range(4):
            cell = rgba[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw]
            bb = bbox_of(cell[:, :, 3])
            cells.append((cell, bb))
        # escala unica por linha: preserva o crescimento do efeito
        dims = [max(bb[2] - bb[0], bb[3] - bb[1]) for _, bb in cells if bb]
        if not dims:
            print("vazio:", name)
            continue
        scale = BOX / max(dims)
        strip = np.zeros((CELL, CELL * 4, 4), np.uint8)
        for col, (cell, bb) in enumerate(cells):
            if bb is None:
                continue
            crop = cell[bb[1]:bb[3], bb[0]:bb[2]]
            hh, ww = crop.shape[:2]
            nw = max(1, min(CELL, int(round(ww * scale))))
            nh = max(1, min(CELL, int(round(hh * scale))))
            small = resize_rgba(crop, nw, nh)
            ox = col * CELL + (CELL - nw) // 2
            oy = (CELL - nh) // 2
            strip[oy:oy + nh, ox:ox + nw] = small
        save(quantize(strip, 28), f"{OUT}/vfx/{name}.png")
        made.append(name)
        print("vfx", name, "ok")

print(f"{len(made)} vfx novos:", " ".join(made))

# ------------------------------------------------------------------ ARENAS
AW, AH = 480, 272


def pixelate(im, w=AW, h=AH, ncolors=64):
    out = im.convert("RGB").resize((w, h), Image.BOX)
    return out.quantize(colors=ncolors, method=Image.MEDIANCUT,
                        dither=Image.NONE).convert("RGB")


def write_sheet(name, frames):
    sheet = Image.new("RGB", (AW, AH * 4))
    for i, fr in enumerate(frames):
        sheet.paste(fr, (0, i * AH))
    sheet.save(f"{OUT}/arenas/{name}_sheet.png", optimize=True)
    print("arena sheet", name, sheet.size)


# 1) arenas novas: grade 2x2 de uma unica arte
NEW_ARENAS = {
    "neodojo": "arena_neodojo_grid",
    "sunken": "arena_sunken_grid",
    "canyon": "arena_canyon_grid",
    "foundry": "arena_foundry_grid",
    "crystal": "arena_crystal_grid",
    "storm": "arena_storm_grid",
}
for name, stem in NEW_ARENAS.items():
    src = f"{SRC}/{stem}.png"
    if not os.path.exists(src):
        print("faltando:", src)
        continue
    im = Image.open(src).convert("RGB")
    w, h = im.size
    cw, ch = w // 2, h // 2
    frames = []
    for r in range(2):
        for c in range(2):
            cell = im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            frames.append(pixelate(cell))
    write_sheet(name, frames)

# 2) arenas antigas: consolida os 4 arquivos soltos em um sheet unico
OLD_ARENAS = ["dojo", "volcano", "orbital", "frozen", "sky"]
for name in OLD_ARENAS:
    files = [f"{OUT}/arenas/{name}_f{i}.png" for i in range(1, 5)]
    if not all(os.path.exists(f) for f in files):
        print("faltando frames de", name)
        continue
    frames = [Image.open(f).convert("RGB").resize((AW, AH), Image.BOX)
              for f in files]
    write_sheet(name, frames)

print("total sheets:", len(glob.glob(f"{OUT}/arenas/*_sheet.png")))
