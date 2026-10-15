#!/usr/bin/env python3
"""Fase D — corta as folhas de pecas modulares (IA) em pecas individuais.

Cada folha e 1024x1024 com grade 4x2 (8 pecas) em fundo magenta #FF00FF.
Pipeline canonico: chroma key magenta -> bbox -> resize BOX -> quantize.
Saida: packages/web/public/parts/<cat><n>.png
"""
import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "packages", "web", "public", "parts")

# categoria -> (prefixo do arquivo cru, altura final em px)
SHEETS = [
    ("head", "pt_heads_a", 46),
    ("headb", "pt_heads_b", 46),
    ("torso", "pt_torsos_a", 54),
    ("torsob", "pt_torsos_b", 54),
    ("arm", "pt_arms", 48),
    ("leg", "pt_legs", 54),
    ("deco", "pt_deco", 50),
]

COLS, ROWS = 4, 2


def chroma(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # magenta: vermelho e azul altos, verde baixo
            if r > 150 and b > 150 and g < 110 and abs(r - b) < 90:
                px[x, y] = (0, 0, 0, 0)
    return im


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    made = []
    for cat, prefix, target_h in SHEETS:
        matches = sorted(glob.glob(os.path.join(ROOT, "assets", "raw", f"{prefix}_*.png")))
        if not matches:
            print(f"!! folha ausente: {prefix}")
            continue
        sheet = Image.open(matches[-1]).convert("RGBA")
        W, H = sheet.size
        cw, ch = W // COLS, H // ROWS
        n = 0
        for ry in range(ROWS):
            for cx in range(COLS):
                cell = sheet.crop((cx * cw, ry * ch, (cx + 1) * cw, (ry + 1) * ch))
                cell = chroma(cell)
                bb = cell.getbbox()
                if not bb:
                    continue
                cell = cell.crop(bb)
                # margem de seguranca: descarta cortes minusculos (ruido)
                if cell.height < 40 or cell.width < 20:
                    continue
                scale = target_h / cell.height
                nw = max(8, round(cell.width * scale))
                cell = cell.resize((nw, target_h), Image.BOX)
                alpha = cell.getchannel("A").point(lambda v: 255 if v > 96 else 0)
                cell.putalpha(alpha)
                q = cell.convert("RGB").quantize(colors=48, method=Image.MEDIANCUT).convert("RGBA")
                q.putalpha(alpha)
                path = os.path.join(OUT, f"{cat}{n}.png")
                q.save(path)
                made.append((f"{cat}{n}", q.size))
                n += 1
        print(f"{cat}: {n} pecas")
    print(f"total {len(made)} pecas em {OUT}")
    for name, size in made:
        print(" ", name, size)


if __name__ == "__main__":
    main()
