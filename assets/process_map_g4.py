#!/usr/bin/env python3
"""Fase G4 — recorta folhas 4x4 geradas por IA em tiles/props individuais.

Folhas de entrada: /home/user/tmpwork/g4/{tiles_*,props_*}.png
  - fundo e gutters em magenta puro (#FF00FF)
  - grade 4x4 de 16 celulas

Saida:
  tiles_X.png -> packages/web/public/map/tiles/X.png
      atlas horizontal de 16 tiles de TILE px (16*TILE x TILE), opaco
  props_X.png -> packages/web/public/map/props/X.png
      atlas horizontal de 16 props de PROP px, com alfa (magenta removido)

Chroma-key estrito (validado na fase G3):
    r>180 and b>180 and g<95 and abs(r-b)<70
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

SRC = Path("/home/user/tmpwork/g4")
OUT_TILES = Path("/home/user/mecha-champions/packages/web/public/map/tiles")
OUT_PROPS = Path("/home/user/mecha-champions/packages/web/public/map/props")

TILE = 32  # tile de terreno final
PROP = 48  # prop final


def magenta_mask(im: Image.Image):
    """Retorna (mask, w, h) onde mask[i] = True se pixel i eh chroma magenta."""
    rgb = im.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    mask = bytearray(w * h)
    for y in range(h):
        base = y * w
        for x in range(w):
            r, g, b = px[x, y]
            if r > 180 and b > 180 and g < 95 and abs(r - b) < 70:
                mask[base + x] = 1
    return mask, w, h


def runs(flags: list[bool]) -> list[tuple[int, int]]:
    """Agrupa indices True consecutivos em (inicio, fim_exclusivo)."""
    out: list[tuple[int, int]] = []
    start = None
    for i, f in enumerate(flags):
        if f and start is None:
            start = i
        elif not f and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(flags)))
    return out


def bands(mask: bytearray, w: int, h: int, axis: str, want: int) -> list[tuple[int, int]]:
    """Encontra as `want` faixas de conteudo (nao-magenta) ao longo de um eixo."""
    if axis == "x":
        n, other = w, h
        frac = [
            sum(mask[y * w + i] for y in range(other)) / other for i in range(n)
        ]
    else:
        n, other = h, w
        frac = [
            sum(mask[i * w + x] for x in range(other)) / other for i in range(n)
        ]

    # linha eh separador se a maioria for magenta
    content = runs([f < 0.55 for f in frac])
    # descarta faixas finas (ruido de borda)
    content = [c for c in content if c[1] - c[0] > n * 0.05]
    if len(content) != want:
        # fallback: divisao uniforme
        print(f"    ! {axis}: {len(content)} faixas (esperado {want}) — usando grade uniforme")
        step = n / want
        return [(round(i * step), round((i + 1) * step)) for i in range(want)]
    return content


def cells(path: Path) -> list[Image.Image]:
    """Recorta a folha em 16 celulas na ordem de leitura."""
    im = Image.open(path).convert("RGBA")
    mask, w, h = magenta_mask(im)
    cols = bands(mask, w, h, "x", 4)
    rows = bands(mask, w, h, "y", 4)
    out: list[Image.Image] = []
    for y0, y1 in rows:
        for x0, x1 in cols:
            out.append(im.crop((x0, y0, x1, y1)))
    return out


def strip_chroma(im: Image.Image) -> Image.Image:
    """Zera o alfa dos pixels de chroma magenta."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and r > 180 and b > 180 and g < 95 and abs(r - b) < 70:
                px[x, y] = (0, 0, 0, 0)
    return im


def trim_alpha(im: Image.Image) -> Image.Image:
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def fit(im: Image.Image, size: int, keep_alpha: bool) -> Image.Image:
    """Redimensiona para caber em size x size, nearest, centrado."""
    if keep_alpha:
        im = trim_alpha(im)
        w, h = im.size
        s = min(size / w, size / h)
        nw, nh = max(1, round(w * s)), max(1, round(h * s))
        small = im.resize((nw, nh), Image.NEAREST)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(small, ((size - nw) // 2, size - nh), small)  # assenta no chao
        return canvas
    return im.resize((size, size), Image.NEAREST).convert("RGBA")


def atlas(frames: list[Image.Image], size: int) -> Image.Image:
    sheet = Image.new("RGBA", (size * len(frames), size), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * size, 0), f)
    return sheet


def main() -> int:
    OUT_TILES.mkdir(parents=True, exist_ok=True)
    OUT_PROPS.mkdir(parents=True, exist_ok=True)

    sheets = sorted(SRC.glob("tiles_*.png")) + sorted(SRC.glob("props_*.png"))
    if not sheets:
        print("nenhuma folha encontrada em", SRC)
        return 1

    for path in sheets:
        is_prop = path.name.startswith("props_")
        name = path.stem.split("_", 1)[1]
        size = PROP if is_prop else TILE
        out_dir = OUT_PROPS if is_prop else OUT_TILES
        print(f"[{path.name}] -> {out_dir.name}/{name}.png")

        raw = cells(path)
        if len(raw) != 16:
            print(f"    ! {len(raw)} celulas, esperado 16 — pulando")
            continue

        frames = []
        for c in raw:
            c = strip_chroma(c)
            frames.append(fit(c, size, keep_alpha=is_prop))

        sheet = atlas(frames, size)
        sheet.save(out_dir / f"{name}.png")
        print(f"    ok {sheet.size[0]}x{sheet.size[1]} ({len(frames)} quadros de {size}px)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
