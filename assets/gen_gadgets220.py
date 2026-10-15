#!/usr/bin/env python3
"""Gera os 100 gadgets dos robos 121-220 (defs + arte) de forma idempotente.

Arte: reaproveita um icone existente do mesmo `kind` e aplica rotacao de matiz
deterministica pelo elemento, mantendo o pixel art original.
Defs: injeta bloco marcado em game/gadgets.ts.
"""
import colorsys
import hashlib
import json

from PIL import Image

ROSTER = "/home/user/mecha-champions/assets/roster220.json"
GADG = "/home/user/mecha-champions/packages/web/src/web/game/gadgets.ts"
ART = "/home/user/mecha-champions/packages/web/public/gadgets"
BEGIN = "  // --- GADGETS 220 ---\n"
END = "  // --- FIM GADGETS 220 ---\n"

KINDS = ["power", "guard", "speed", "vitality", "reactor", "leech", "thorns",
         "regen", "crit", "phase", "amp", "aegis"]

NOUN = {"power": "PUNHO", "guard": "PLACA", "speed": "PROPULSOR",
        "vitality": "CORACAO", "reactor": "CELULA", "leech": "GARRA",
        "thorns": "ESPINHO", "regen": "COLMEIA", "crit": "VISOR",
        "phase": "MANTO", "amp": "RESSOADOR", "aegis": "BARREIRA"}

DESC = {
    "power": "+{v}% de FORCA em combate.",
    "guard": "+{v}% de DEFESA em combate.",
    "speed": "+{v}% de AGILIDADE em combate.",
    "vitality": "+{v}% de HP maximo.",
    "reactor": "+{v}% de MP maximo.",
    "leech": "Recupera {v}% do dano causado como HP.",
    "thorns": "Reflete {v}% do dano recebido.",
    "regen": "Repara {v}% do HP maximo por turno.",
    "crit": "+{v}% de chance de golpe critico.",
    "phase": "+{v}% de chance de esquiva.",
    "amp": "+{v}% de dano nas habilidades.",
    "aegis": "-{v}% de dano recebido.",
}

BASE_STEP = {
    "power": (9.0, 2.2), "guard": (8.0, 2.0), "speed": (9.0, 2.2),
    "vitality": (11.2, 2.8), "reactor": (13.5, 3.4), "leech": (9.0, 1.7),
    "thorns": (11.2, 2.2), "regen": (4.6, 0.9), "crit": (5.6, 1.1),
    "phase": (4.5, 0.9), "amp": (8.0, 2.0), "aegis": (6.0, 1.2),
}

PRICE = {"bronze": 8000, "silver": 12000, "gold": 18000}
MULT = {"bronze": 0.9, "silver": 1.0, "gold": 1.15}

ADJ = ["MORTIFERO", "ARCANO", "TITANICO", "SPECTRAL", "VORAZ", "SIDERAL",
       "PRIMEVO", "CAUSTICO", "RUNICO", "COLOSSAL", "ETEREO", "FERAL"]


def h(s, salt=""):
    return int(hashlib.md5((s + salt).encode()).hexdigest(), 16)


def hue_shift(im, deg):
    im = im.convert("RGBA")
    px = im.load()
    w, hh = im.size
    d = (deg % 360) / 360.0
    for y in range(hh):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hs, ls, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            r2, g2, b2 = colorsys.hls_to_rgb((hs + d) % 1.0, ls, min(1.0, ss * 1.05))
            px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    return im


src = open(GADG).read()

# fontes de arte existentes por kind (a partir dos defs ja no arquivo)
import re

existing = re.findall(r'robotId: "([a-z0-9]+)", name: "[^"]+", kind: "([a-z]+)"', src)
by_kind = {}
for rid, kind in existing:
    by_kind.setdefault(kind, []).append(rid)

roster = json.load(open(ROSTER))
lines = []
for r in roster:
    rid, name, elem, rar = r["i"], r["n"], r["e"], r["r"]
    kind = KINDS[h(rid, "k") % len(KINDS)]
    base0, step0 = BASE_STEP[kind]
    m = MULT[rar]
    base = round(base0 * m + (h(rid, "b") % 7) * 0.1, 1)
    step = round(step0 * m, 1)
    adj = ADJ[h(rid, "adj") % len(ADJ)]
    gname = f"{NOUN[kind]} {adj}"
    desc = DESC[kind].format(v=base)
    flavor = f"Modulo {adj.lower()} forjado sob medida para {name}."
    lines.append(
        f'  {{ robotId: "{rid}", name: "{gname}", kind: "{kind}", element: "{elem}", '
        f'rarity: "{rar}", base: {base}, step: {step}, price: {PRICE[rar]}, '
        f'desc: "{desc}", flavor: "{flavor}" }},'
    )
    # arte
    pool = by_kind.get(kind) or by_kind["power"]
    srcart = pool[h(rid, "art") % len(pool)]
    out = f"{ART}/{rid}.png"
    im = Image.open(f"{ART}/{srcart}.png")
    deg = h(rid, "hue") % 360
    hue_shift(im, deg).save(out)

if BEGIN in src:
    i, j = src.index(BEGIN), src.index(END) + len(END)
    src = src[:i] + src[j:]
block = BEGIN + "\n".join(lines) + "\n" + END
k = src.index("\n];", src.index("export const GADGETS"))
src = src[:k + 1] + block + src[k + 1:]
open(GADG, "w").write(src)
print("gadgets novos:", len(lines))
