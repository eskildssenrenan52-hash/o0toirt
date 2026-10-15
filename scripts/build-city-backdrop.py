"""Gera os assets do fundo animado da cidade (hub).

Saidas em packages/web/public/city/:
  sky_anim.webp      - folha com 50 quadros do ceu (5 colunas x 10 linhas, 480x270 cada)
  pl_far_city.png    - city_f4 sem as tarjas pretas e com o ceu desvanecido (topo transparente)
  pl_near_city.png   - bg.png com o ceu desvanecido (topo transparente)
  traffic.png        - atlas dos veiculos/aeronaves que cruzam o ceu
e imprime o JSON de recortes do atlas (copiado para components/city-backdrop.ts).

Uso: python scripts/build-city-backdrop.py [pasta_dos_sprites_recortados]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "packages/web/public"
SPRITES = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/user/_view/sprites")

FRAMES = 50
FW, FH = 480, 270
COLS = 5


def ramp_alpha(img: Image.Image, start: float, end: float) -> Image.Image:
    """alpha 0 ate `start` (fracao da altura), sobe suave ate 1 em `end`."""
    a = np.array(img.convert("RGBA")).astype(np.float32)
    h = a.shape[0]
    y = np.arange(h, dtype=np.float32) / h
    k = np.clip((y - start) / max(1e-6, end - start), 0, 1)
    k = k * k * (3 - 2 * k)  # smoothstep
    a[..., 3] *= k[:, None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def build_layers():
    f4 = np.array(Image.open(PUB / "loading/city_f4.png").convert("RGB"))
    rows = f4.mean(axis=(1, 2))
    keep = np.where(rows > 6)[0]
    f4 = Image.fromarray(f4[keep[0] : keep[-1] + 1])
    ramp_alpha(f4, 0.12, 0.5).save(PUB / "city/pl_far_city.png", optimize=True)
    bg = Image.open(PUB / "city/bg.png")
    ramp_alpha(bg, 0.06, 0.42).save(PUB / "city/pl_near_city.png", optimize=True)


def build_sky():
    base = Image.open(PUB / "city/pl_sky.png").convert("RGB").resize((FW, FH), Image.NEAREST)
    b = np.array(base).astype(np.float32)
    r, g, bl = b[..., 0], b[..., 1], b[..., 2]
    lum = 0.3 * r + 0.55 * g + 0.15 * bl
    yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)

    # planeta (centro aproximado na folha 480x270) — fora das mascaras de estrela/aurora
    pcx, pcy, pr = 232, 222, 52
    planet = (xx - pcx) ** 2 + (yy - pcy) ** 2 < (pr + 4) ** 2
    ringband = (np.abs((yy - pcy) - (xx - pcx) * -0.33) < 22) & (np.abs(xx - pcx) < 150) & ~planet

    # estrelas: pixels mais claros que a vizinhanca
    from scipy import ndimage

    med = ndimage.median_filter(lum, size=5)
    star = (lum - med > 22) & ~planet & ~ringband
    lab, n = ndimage.label(star)
    rng = np.random.default_rng(2026)
    phase = rng.random(n + 1) * 2 * math.pi
    freq = rng.integers(1, 4, n + 1).astype(np.float32)
    centers = ndimage.center_of_mass(star, lab, range(1, n + 1))
    peak = ndimage.maximum(lum, lab, range(1, n + 1))
    bright = sorted(range(n), key=lambda i: -peak[i])[:14]

    aurora = (g > 70) & (bl > 120) & (g > r * 0.9) & ~planet & ~star
    nebula = (r > 80) & (bl > 100) & (g < r * 0.8) & ~planet & ~star & ~ringband & (yy < 200)
    ring = ringband & (r > 110) & (bl > 160)

    meteors = [
        # (frame inicial, duracao, x0, y0, dx, dy)
        (5, 11, 60, 18, 210, 70),
        (29, 9, 420, 12, -180, 66),
    ]

    sheet = Image.new("RGB", (FW * COLS, FH * (FRAMES // COLS)))
    for f in range(FRAMES):
        t = f / FRAMES
        out = b.copy()
        # aurora: onda de brilho viajando
        wave = 0.82 + 0.3 * np.sin(2 * math.pi * (xx / 150 + yy / 80 - 2 * t))
        wave2 = 0.92 + 0.12 * np.sin(2 * math.pi * (xx / 47 - 3 * t))
        k = np.where(aurora, wave * wave2, 1.0)
        out = out * k[..., None]
        lift = np.where(aurora, np.clip(wave - 0.98, 0, 1), 0)
        out[..., 1] += lift * 70
        out[..., 2] += lift * 90
        # nebulosa respirando
        kn = 0.9 + 0.14 * np.sin(2 * math.pi * (t + xx / 260))
        out = np.where(nebula[..., None], out * kn[..., None], out)
        # brilho correndo pelo anel do planeta
        gx = pcx - 150 + 300 * t
        glint = np.exp(-(((xx - gx) / 10) ** 2))
        out = out + np.where(ring, glint * 70, 0)[..., None]
        # estrelas piscando
        tw = 0.55 + 0.75 * (0.5 + 0.5 * np.sin(2 * math.pi * freq * t + phase))
        kst = np.where(star, tw[lab], 1.0)
        out = np.where(star[..., None], out * kst[..., None] + (kst[..., None] - 1) * 30, out)
        frame = Image.fromarray(out.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(frame)
        # cruz de brilho nas estrelas mais fortes, no pico
        for i in bright:
            s = 0.5 + 0.5 * math.sin(2 * math.pi * freq[i + 1] * t + phase[i + 1])
            if s > 0.78:
                cy, cx = centers[i]
                cx, cy = int(round(cx)), int(round(cy))
                c = (200, 220, 255) if s > 0.92 else (140, 160, 235)
                ln = 3 if s > 0.92 else 2
                d.line([(cx - ln, cy), (cx + ln, cy)], fill=c)
                d.line([(cx, cy - ln), (cx, cy + ln)], fill=c)
        # estrelas cadentes
        for f0, dur, x0, y0, dx, dy in meteors:
            p = (f - f0) / dur
            if 0 <= p <= 1:
                hx, hy = x0 + dx * p, y0 + dy * p
                tail = 26
                ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
                fade = 1 - max(0, p - 0.7) / 0.3
                for j in range(tail):
                    a = (1 - j / tail) * fade
                    px, py = int(hx - ux * j), int(hy - uy * j)
                    if 0 <= px < FW and 0 <= py < FH:
                        o = frame.getpixel((px, py))
                        col = (int(o[0] + (230 - o[0]) * a), int(o[1] + (240 - o[1]) * a), int(o[2] + (255 - o[2]) * a))
                        frame.putpixel((px, py), col)
                if 0 <= int(hx) < FW and 0 <= int(hy) < FH:
                    frame.putpixel((int(hx), int(hy)), (255, 255, 255))
        sheet.paste(frame, ((f % COLS) * FW, (f // COLS) * FH))
    sheet.save(PUB / "city/sky_anim.webp", quality=88, method=6)


# sprite -> (largura final no atlas, virado para a direita?)
TRAFFIC = {
    "blimp": ("s_0.png", 480, True),
    "cargo": ("s_1.png", 500, False),
    "train": ("s_2.png", 540, True),
    "carrier": ("s_3.png", 560, True),
    "car": ("v_0.png", 200, True),
    "taxi": ("v_1.png", 196, True),
    "truck": ("v_4.png", 280, True),
    "drone": ("v_5.png", 104, True),
    "jets": ("v_7.png", 170, True),
}


def build_atlas():
    items = []
    for key, (fn, tw, right) in TRAFFIC.items():
        im = Image.open(SPRITES / fn).convert("RGBA")
        th = round(im.height * tw / im.width)
        im = im.resize((tw, th), Image.LANCZOS)
        items.append((key, im, right))
    # empacotamento em prateleiras
    W = 1100
    x = y = rowh = 0
    pos = {}
    for key, im, right in sorted(items, key=lambda t: -t[1].height):
        if x + im.width > W:
            x, y, rowh = 0, y + rowh + 2, 0
        pos[key] = (x, y, im.width, im.height, right)
        x += im.width + 2
        rowh = max(rowh, im.height)
    atlas = Image.new("RGBA", (W, y + rowh))
    for key, im, _ in items:
        px, py, *_ = pos[key]
        atlas.alpha_composite(im, (px, py))
    atlas.save(PUB / "city/traffic.png", optimize=True)
    print(json.dumps({k: {"x": v[0], "y": v[1], "w": v[2], "h": v[3], "right": v[4]} for k, v in pos.items()}))


if __name__ == "__main__":
    build_layers()
    build_sky()
    build_atlas()
