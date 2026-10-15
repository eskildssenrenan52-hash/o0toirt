#!/usr/bin/env python3
"""Processa assets do mapa espacial: fundo + estacoes."""
import glob
import os

import numpy as np
from PIL import Image

import sys
sys.path.insert(0, "/home/user/mecha-champions/assets")
from process_robots100 import (  # noqa: E402
    OUT, RAW, bbox_of, find, fit_into, grid_cells, quantize, resize_rgba, save, to_rgba,
)

os.makedirs(f"{OUT}/map", exist_ok=True)

# fundo estrelado -> 640x427 pixelado (repetido via CSS)
bg = Image.open(find("map_space_bg*.png")).convert("RGB")
w, h = 480, int(480 * bg.size[1] / bg.size[0])
small = bg.resize((w, h), Image.BOX).quantize(colors=48, dither=Image.NONE).convert("RGB")
small.save(f"{OUT}/map/space_bg.png", optimize=True)
print("bg", small.size)

SHEETS = [
    ("map_stations_a*.png", ["station_dojo_1", "station_dojo_2", "station_dojo_3",
                             "station_volcano_1", "station_volcano_2", "station_volcano_3",
                             "station_orbital_1", "station_orbital_2", "station_orbital_3"]),
    ("map_stations_b*.png", ["station_frozen_1", "station_frozen_2", "station_frozen_3",
                             "station_sky_1", "station_sky_2", "station_sky_3",
                             "station_champion_1", "station_champion_2", "station_champion_3"]),
]

for pat, names in SHEETS:
    rgba = to_rgba(Image.open(find(pat)))
    for i, cell in enumerate(grid_cells(rgba, 3, 3)):
        out = fit_into(cell, 124, 124, 128, 128, "center")
        save(quantize(out, 40), f"{OUT}/map/{names[i]}.png")
        print("station", names[i], "ok")
