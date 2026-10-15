#!/usr/bin/env python3
"""Acrescenta 100 torneios (1 por robo 121-220) em game/tournaments_extra.ts.

Idempotente: usa marcadores // --- TORNEIOS 220 --- / // --- FIM TORNEIOS 220 ---
e reinjeta o bloco. Nao mexe nos 100 torneios anteriores (ids 21-120).
"""
import hashlib
import json
import re

ROSTER220 = "/home/user/mecha-champions/assets/roster220.json"
ROSTER100 = "/home/user/mecha-champions/assets/roster100.json"
OUT = "/home/user/mecha-champions/packages/web/src/web/game/tournaments_extra.ts"
BEGIN = "  // --- TORNEIOS 220 ---\n"
END = "  // --- FIM TORNEIOS 220 ---\n"

BASE20 = ["aurorion", "ferrovax", "cryolance", "voltronin", "pyrokaiser", "terrabyte",
          "zephyrblade", "nullshade", "acidra", "gravitus", "chronowake", "bioreaper",
          "stormfang", "quartzine", "hydroknight", "emberfox", "ironmonk", "nebulon",
          "titanox", "magnavore"]

ARENA_RULES = [
    ("volcano", ["FOGO", "BRASA", "VULCAO", "FORJA", "CINZAS", "PLASMA", "METEORO",
                 "OBSIDIANA", "RUINA", "FERRUGEM", "MAGMA", "SOLAR", "INFERNO",
                 "PIRO", "LAVA", "CALDEIRA", "CARVAO", "FENIX"]),
    ("frozen", ["GELO", "NEVE", "TUNDRA", "AGUA", "RECIFE", "CRISTAL", "ESPELHO",
                "PANTANO", "TOXINA", "ACIDO", "AMBAR", "MARE", "ABISSAL", "GEADA",
                "ORVALHO", "SAL", "VIDRO", "PEROLA", "CORAL", "NEVOA"]),
    ("orbital", ["COSMICO", "VAZIO", "ABISSO", "BURACO NEGRO", "QUANTUM", "PULSAR",
                 "NEBULOSA", "ANEL", "GRAVIDADE", "MAGNETISMO", "TEMPO", "LUA",
                 "ECLIPSE", "NEON", "GRAFENO", "ZENITE", "ORBITA", "ESTRELA",
                 "COMETA", "SINGULARIDADE", "PRISMA", "FOTON", "ANTIMATERIA",
                 "ORACULO", "PARADOXO", "AURORA", "ESPECTRO", "RADIO"]),
    ("sky", ["VENTO", "NUVEM", "TEMPESTADE", "TROVAO", "LUZ", "SOL", "CICLONE",
             "PLUMA", "TUFAO", "RAIO", "ZEFIRO", "ASA", "TROPOSFERA"]),
    ("dojo", ["TERRA", "FERRO", "TITA", "JADE", "BIO", "SELVA", "OSSO", "SOMBRA",
              "AREIA", "DESERTO", "OURO", "PEDRA", "RAIZ", "FUNGO", "BASALTO",
              "BRONZE", "COBRE", "ACO", "MUSGO", "ESPORO", "GRANITO", "ARGILA",
              "SANGUE", "TOTEM", "RUNA", "MADEIRA", "COURO", "PRESA"]),
]

ROUND_NAMES = ["PRELIMINAR", "OITAVAS", "QUARTAS", "SEMIFINAL"]
ITEM_BY_TIER = [("repair_kit", 3), ("energy_cell", 3), ("shield_chip", 2),
                ("mega_repair", 3), ("power_chip", 2), ("revive_core", 3)]


def h(s, salt=""):
    return int(hashlib.md5((s + salt).encode()).hexdigest(), 16)


def arena_for(elem):
    for a, keys in ARENA_RULES:
        if elem in keys:
            return a
    return "dojo"


roster = json.load(open(ROSTER220))
prev = json.load(open(ROSTER100))
tier = {"bronze": 0, "silver": 1, "gold": 2}
order = sorted(roster, key=lambda r: (tier[r["r"]] * 1000 + h(r["i"], "ord2") % 900))

# robos ja existentes no jogo (120) sempre disponiveis como sparring
existing = BASE20 + [r["i"] for r in prev]
pool_by_arena = {}
for r in prev:
    pool_by_arena.setdefault(arena_for(r["e"]), []).append(r["i"])
for r in roster:
    pool_by_arena.setdefault(arena_for(r["e"]), []).append(r["i"])

out = []
for n, r in enumerate(order):
    rid = r["i"]
    lvl = max(1, min(99, round(2 + 97 * (n / (len(order) - 1)) ** 1.15)))
    arena = arena_for(r["e"])
    nfights = 3 if lvl < 25 else (4 if lvl < 70 else 5)
    unlocked = [x["i"] for x in order[:n]] + existing
    same = [x for x in pool_by_arena.get(arena, []) if x in unlocked]
    fights = []
    for f in range(nfights):
        count = min(2 + (f >= nfights - 1), 3)
        picks = []
        for c in range(count):
            src = same if (same and (h(rid, f"a{f}{c}") % 3)) else unlocked
            picks.append(src[h(rid, f"e{f}{c}") % len(src)])
        boss = f == nfights - 1
        enemies = [{"id": pid, "level": lvl + f, "trained": f} for pid in picks]
        if boss:
            enemies.append({"id": rid, "level": min(99, lvl + f + 2),
                            "trained": f + 1})
        name = f"FINAL — {r['n']}" if boss else ROUND_NAMES[min(f, 3)]
        fights.append({"name": name, "enemies": enemies})
    xp = round(135 * lvl ** 1.1)
    gold = round(xp * 5) + 400
    item, qty = ITEM_BY_TIER[min(5, lvl // 17)]
    # segunda metade do mapa espacial: y a partir de 2900
    per = 12
    row, col = n // per, n % per
    if row % 2:
        col = per - 1 - col
    x = 320 + col * 270 + (h(rid, "jx") % 90) - 45
    y = 2900 + row * 250 + (h(rid, "jy") % 80) - 40
    station = f"station_{arena}_{1 + h(rid, 'st') % 3}"
    out.append({
        "id": f"t_{rid}",
        "name": f"COPA {r['n']}",
        "arena": arena,
        "element": r["e"],
        "desc": (f"Circuito de {r['e'].title()} — enfrente {r['n']} na final "
                 "e conquiste seu chassi."),
        "requiredLevel": lvl,
        "fights": fights,
        "reward": {"gold": gold, "xp": xp, "robot": rid, "item": item,
                   "itemQty": qty},
        "replayGold": round(gold * 0.26),
        "station": station,
        "x": x,
        "y": y,
    })


def ts(v, ind=0):
    p = "  " * ind
    if isinstance(v, dict):
        inner = ",\n".join(f"{p}  {k}: {ts(val, ind + 1)}" for k, val in v.items())
        return "{\n" + inner + f",\n{p}}}"
    if isinstance(v, list):
        inner = ",\n".join(f"{p}  {ts(x, ind + 1)}" for x in v)
        return "[\n" + inner + f",\n{p}]"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(v)


src = open(OUT).read()
# remove bloco anterior se existir
if BEGIN in src:
    i, j = src.index(BEGIN), src.index(END) + len(END)
    src = src[:i] + src[j:]

body = ",\n".join("  " + ts(t, 1) for t in out)
block = BEGIN + body + ",\n" + END
marker = "\n];\n"
assert src.rstrip().endswith("];"), "formato inesperado em tournaments_extra.ts"
k = src.rindex(marker)
src = src[:k + 1] + block + src[k + 1:]
open(OUT, "w").write(src)
print("torneios novos:", len(out), "| niveis:", out[0]["requiredLevel"], "->",
      out[-1]["requiredLevel"], "| ymax:", max(t["y"] for t in out))
