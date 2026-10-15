#!/usr/bin/env python3
"""Processa as artes dos cards: crop central quadrado -> downscale BOX 128x128
-> quantizacao pixel art -> /public/cards/<id>.png"""
import glob
import os

from PIL import Image

RAW = "/home/user/mecha-champions/assets/raw"
OUT = "/home/user/mecha-champions/packages/web/public/cards"
SIZE = 128

os.makedirs(OUT, exist_ok=True)

done = 0
for path in sorted(glob.glob(f"{RAW}/card_*.png")):
    base = os.path.basename(path)
    stem = base[len("card_"):].rsplit("_", 1)[0]
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    im = im.resize((SIZE, SIZE), Image.BOX)
    im = im.quantize(colors=48, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    im.save(f"{OUT}/{stem}.png")
    done += 1

print("cards processados:", done)
