#!/usr/bin/env python3
"""Pipeline de assets pixel art: chroma key magenta -> alpha, fatiar sheets,
downscale BOX + quantizacao de paleta, export para packages/web/public/."""
import glob
import json
import os
import subprocess

import numpy as np
from PIL import Image

RAW = "/home/user/mecha-champions/assets/raw"
OUT = "/home/user/mecha-champions/packages/web/public"

os.makedirs(f"{OUT}/robots", exist_ok=True)
os.makedirs(f"{OUT}/ui", exist_ok=True)
os.makedirs(f"{OUT}/vfx", exist_ok=True)
os.makedirs(f"{OUT}/arenas", exist_ok=True)


def find(pattern):
    m = sorted(glob.glob(os.path.join(RAW, pattern)))
    if not m:
        raise SystemExit(f"nao encontrado: {pattern}")
    return m[0]


def bg_mask(arr):
    """True onde e fundo magenta."""
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    strong = (r > 110) & (b > 110) & (g < np.minimum(r, b) * 0.62)
    return strong


def to_rgba(im):
    arr = np.asarray(im.convert("RGB")).astype(np.uint8)
    m = bg_mask(arr)
    a = np.where(m, 0, 255).astype(np.uint8)
    out = np.dstack([arr, a])
    return out


def bbox_of(alpha):
    ys, xs = np.nonzero(alpha > 8)
    if len(ys) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def resize_rgba(rgba, w, h):
    """Downscale com premultiply para evitar halo."""
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


def quantize(rgba, ncolors=48):
    a = rgba[:, :, 3]
    rgb = rgba[:, :, :3].copy()
    # evita que pixels transparentes poluam a paleta
    if (a > 0).any():
        med = rgb[a > 0].reshape(-1, 3).mean(axis=0).astype(np.uint8)
        rgb[a == 0] = med
    q = Image.fromarray(rgb, "RGB").quantize(
        colors=ncolors, method=Image.MEDIANCUT, dither=Image.NONE
    ).convert("RGB")
    out = np.dstack([np.asarray(q).astype(np.uint8), a])
    # limpa qualquer residuo de magenta visivel
    resid = bg_mask(out[:, :, :3]) & (a > 0)
    out[resid, 3] = 0
    return out


def save(rgba, path):
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def grid_cells(rgba, cols, rows):
    h, w = rgba.shape[:2]
    cw, ch = w // cols, h // rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            cells.append(rgba[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw])
    return cells


def fit_into(cell_rgba, box_w, box_h, out_w, out_h, anchor="bottom"):
    """Recorta bbox, escala para caber, cola em canvas fixo."""
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


# ---------------------------------------------------------------- ROBOTS
ROBOTS = [
    ("aurorion", "AURORION", "robot_01_aurorion*.png"),
    ("ferrovax", "FERROVAX", "robot_02_ferrovax*.png"),
    ("cryolance", "CRYOLANCE", "robot_03_cryolance*.png"),
    ("voltronin", "VOLT RONIN", "robot_04_voltronin*.png"),
    ("pyrokaiser", "PYROKAISER", "robot_05_pyrokaiser*.png"),
    ("terrabyte", "TERRABYTE", "robot_06_terrabyte*.png"),
    ("zephyrblade", "ZEPHYRBLADE", "robot_07_zephyrblade*.png"),
    ("nullshade", "NULLSHADE", "robot_08_nullshade*.png"),
    ("acidra", "ACIDRA", "robot_09_acidra*.png"),
    ("gravitus", "GRAVITUS", "robot_10_gravitus*.png"),
    ("chronowake", "CHRONOWAKE", "robot_11_chronowake*.png"),
    ("bioreaper", "BIOREAPER", "robot_12_bioreaper*.png"),
    ("stormfang", "STORMFANG", "robot_13_stormfang*.png"),
    ("quartzine", "QUARTZINE", "robot_14_quartzine*.png"),
    ("hydroknight", "HYDROKNIGHT", "robot_15_hydroknight*.png"),
    ("emberfox", "EMBERFOX", "robot_16_emberfox*.png"),
    ("ironmonk", "IRONMONK", "robot_17_ironmonk*.png"),
    ("nebulon", "NEBULON", "robot_18_nebulon*.png"),
    ("titanox", "TITANOX", "robot_19_titanox*.png"),
    ("magnavore", "MAGNAVORE", "robot_20_magnavore*.png"),
]

FRAME = 128          # celula final por frame
FRAME_BOX = (120, 122)
manifest = {"frame": FRAME, "frames": 16, "robots": []}

for rid, name, pat in ROBOTS:
    src = find(pat)
    rgba = to_rgba(Image.open(src))
    cells = grid_cells(rgba, 4, 4)
    # bbox UNIAO -> mantem alinhamento entre frames
    boxes = [bbox_of(c[:, :, 3]) for c in cells]
    boxes = [b for b in boxes if b]
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
        oy = FRAME - nh
        strip[oy:oy + nh, ox:ox + nw] = small
    strip = quantize(strip, 56)
    save(strip, f"{OUT}/robots/{rid}.png")
    # retrato = frame 0 recortado
    portrait_cell = strip[:, 0:FRAME]
    save(fit_into(portrait_cell, 60, 60, 64, 64, "center"),
         f"{OUT}/robots/{rid}_face.png")
    manifest["robots"].append({"id": rid, "name": name})
    print("robot", rid, "ok")

# ---------------------------------------------------------------- ICONS
ICONS = ["fist", "shield", "bolt", "heart",
         "battery", "coins", "trophy", "star",
         "arrowup", "lock", "check", "cross",
         "gear", "flame", "drop", "skull"]
rgba = to_rgba(Image.open(find("ui_icons*.png")))
for i, cell in enumerate(grid_cells(rgba, 4, 4)):
    out = fit_into(cell, 30, 30, 32, 32, "center")
    save(quantize(out, 24), f"{OUT}/ui/icon_{ICONS[i]}.png")
print("icons ok")

# ---------------------------------------------------------------- BUTTONS
BTN = ["btn_wide", "btn_wide_pressed", "btn_wide_disabled",
       "btn_sq", "btn_sq_pressed", "btn_sq_active",
       "btn_primary", "btn_primary_pressed", "btn_primary_active",
       "tab_off", "tab_on", "btn_close"]
rgba = to_rgba(Image.open(find("ui_buttons*.png")))
for i, cell in enumerate(grid_cells(rgba, 3, 4)):
    bb = bbox_of(cell[:, :, 3])
    if bb is None:
        continue
    crop = cell[bb[1]:bb[3], bb[0]:bb[2]]
    ch, cw = crop.shape[:2]
    scale = 56 / ch
    small = resize_rgba(crop, max(1, int(round(cw * scale))), 56)
    save(quantize(small, 32), f"{OUT}/ui/{BTN[i]}.png")
print("buttons ok")

# ---------------------------------------------------------------- BARS
BARS = ["bar_frame", "bar_hp", "bar_mp", "bar_xp"]
rgba = to_rgba(Image.open(find("ui_bars*.png")))
from scipy import ndimage as _nd  # noqa: E402

_lbl, _n = _nd.label(_nd.binary_dilation(rgba[:, :, 3] > 8, iterations=4))
_boxes = []
for s in _nd.find_objects(_lbl):
    ys, xs = s
    if (ys.stop - ys.start) < 40 or (xs.stop - xs.start) < 300:
        continue
    _boxes.append((ys.start, ys.stop, xs.start, xs.stop))
_boxes.sort()
for i, (y0, y1, x0, x1) in enumerate(_boxes[:4]):
    crop = rgba[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    scale = 22 / ch
    small = resize_rgba(crop, max(1, int(round(cw * scale))), 22)
    save(quantize(small, 20), f"{OUT}/ui/{BARS[i]}.png")
    print("bar", BARS[i], cw, ch)
print("bars ok")

# ---------------------------------------------------------------- DECO
DECO = ["deco_corner", "deco_divider", "deco_divider2",
        "frame_bronze", "frame_silver", "frame_gold",
        "deco_banner", "deco_badge", "deco_dots"]
rgba = to_rgba(Image.open(find("ui_deco*.png")))
for i, cell in enumerate(grid_cells(rgba, 3, 3)):
    bb = bbox_of(cell[:, :, 3])
    if bb is None:
        continue
    crop = cell[bb[1]:bb[3], bb[0]:bb[2]]
    ch, cw = crop.shape[:2]
    scale = min(96 / cw, 96 / ch)
    small = resize_rgba(crop, max(1, int(round(cw * scale))),
                        max(1, int(round(ch * scale))))
    save(quantize(small, 28), f"{OUT}/ui/{DECO[i]}.png")
print("deco ok")

# ---------------------------------------------------------------- PANELS
# posicoes irregulares -> componentes por projecao de alpha
rgba = to_rgba(Image.open(find("ui_panels*.png")))
alpha = rgba[:, :, 3] > 8
from scipy import ndimage  # noqa: E402

lbl, n = ndimage.label(ndimage.binary_dilation(alpha, iterations=3))
comps = []
for s in ndimage.find_objects(lbl):
    ys, xs = s
    h, w = ys.stop - ys.start, xs.stop - xs.start
    if h < 60 or w < 60:
        continue
    comps.append((w * h, xs.start, ys.start, xs.stop, ys.stop, w, h))
comps.sort(reverse=True)
names = ["panel_large", "panel_card", "panel_square", "panel_strip"]
# ordena: maior area = large; depois por aspecto
sized = []
for c in comps[:4]:
    _, x0, y0, x1, y1, w, h = c
    sized.append((w, h, x0, y0, x1, y1))
sized.sort(key=lambda t: -(t[0] * t[1]))
label_by_shape = []
for w, h, x0, y0, x1, y1 in sized:
    ar = w / h
    if ar > 1.7:
        nm = "panel_strip"
    elif ar < 0.85:
        nm = "panel_card"
    else:
        nm = None
    label_by_shape.append([nm, w, h, x0, y0, x1, y1])
squareish = [e for e in label_by_shape if e[0] is None]
squareish.sort(key=lambda e: -(e[1] * e[2]))
for i, e in enumerate(squareish):
    e[0] = "panel_large" if i == 0 else "panel_square"
for nm, w, h, x0, y0, x1, y1 in label_by_shape:
    crop = rgba[y0:y1, x0:x1]
    scale = min(240 / w, 240 / h)
    small = resize_rgba(crop, max(1, int(round(w * scale))),
                        max(1, int(round(h * scale))))
    save(quantize(small, 24), f"{OUT}/ui/{nm}.png")
    print("panel", nm, w, h)

# ---------------------------------------------------------------- VFX
VFX_A = ["impact", "slash", "explosion", "heal"]
VFX_B = ["shield", "levelup", "void", "thunder"]
for pat, names_ in ((find("vfx_sheet_a*.png"), VFX_A),
                    (find("vfx_sheet_b*.png"), VFX_B)):
    rgba = to_rgba(Image.open(pat))
    cells = grid_cells(rgba, 4, 4)
    for row in range(4):
        strip = np.zeros((96, 96 * 4, 4), np.uint8)
        for col in range(4):
            cell = cells[row * 4 + col]
            f = fit_into(cell, 92, 92, 96, 96, "center")
            strip[:, col * 96:(col + 1) * 96] = f
        save(quantize(strip, 28), f"{OUT}/vfx/{names_[row]}.png")
print("vfx ok")

# ---------------------------------------------------------------- LOGO
rgba = to_rgba(Image.open(find("ui_logo*.png")))
bb = bbox_of(rgba[:, :, 3])
crop = rgba[bb[1]:bb[3], bb[0]:bb[2]]
h, w = crop.shape[:2]
scale = 380 / w
save(quantize(resize_rgba(crop, 380, max(1, int(round(h * scale)))), 40),
     f"{OUT}/ui/logo.png")
print("logo ok")

# ---------------------------------------------------------------- BACKGROUNDS
def pixelate_bg(src, dst, w=480, h=272, ncolors=64):
    im = Image.open(src).convert("RGB").resize((w, h), Image.BOX)
    im = im.quantize(colors=ncolors, method=Image.MEDIANCUT,
                     dither=Image.NONE).convert("RGB")
    im.save(dst, optimize=True)


pixelate_bg(find("bg_menu*.png"), f"{OUT}/ui/bg_menu.png")
print("bg_menu ok")

ARENAS = ["dojo", "volcano", "orbital", "frozen", "sky"]
for a in ARENAS:
    for f in range(1, 5):
        src = find(f"arena_{a}_f{f}_*.png")
        pixelate_bg(src, f"{OUT}/arenas/{a}_f{f}.png")
    # mp4 4fps como artefato de referencia
    lst = f"/tmp/{a}_frames.txt"
    with open(lst, "w") as fh:
        for _ in range(6):
            for f in range(1, 5):
                fh.write(f"file '{OUT}/arenas/{a}_f{f}.png'\nduration 0.25\n")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-vf", "scale=960:544:flags=neighbor", "-r", "4",
         "-pix_fmt", "yuv420p", f"/home/user/mecha-champions/assets/{a}_4fps.mp4"],
        check=False)
    print("arena", a, "ok")

manifest["arenas"] = ARENAS
with open(f"{OUT}/robots/manifest.json", "w") as fh:
    json.dump(manifest, fh, indent=2)
print("DONE")
