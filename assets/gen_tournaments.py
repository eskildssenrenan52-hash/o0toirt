#!/usr/bin/env python3
"""Gera os 100 torneios novos (1 por robo novo) em game/tournaments_extra.ts."""
import hashlib
import json
import math

ROSTER = "/home/user/mecha-champions/assets/roster100.json"
OUT = "/home/user/mecha-champions/packages/web/src/web/game/tournaments_extra.ts"

BASE20 = ["aurorion", "ferrovax", "cryolance", "voltronin", "pyrokaiser", "terrabyte",
          "zephyrblade", "nullshade", "acidra", "gravitus", "chronowake", "bioreaper",
          "stormfang", "quartzine", "hydroknight", "emberfox", "ironmonk", "nebulon",
          "titanox", "magnavore"]

ARENA_RULES = [
    ("volcano", ["FOGO", "BRASA", "VULCAO", "FORJA", "CINZAS", "PLASMA", "METEORO",
                 "OBSIDIANA", "RUINA", "FERRUGEM"]),
    ("frozen", ["GELO", "NEVE", "TUNDRA", "AGUA", "RECIFE", "CRISTAL", "ESPELHO",
                "PANTANO", "TOXINA", "ACIDO", "AMBAR"]),
    ("orbital", ["COSMICO", "VAZIO", "ABISSO", "BURACO NEGRO", "QUANTUM", "PULSAR",
                 "NEBULOSA", "ANEL", "GRAVIDADE", "MAGNETISMO", "TEMPO", "LUA",
                 "ECLIPSE", "NEON", "GRAFENO"]),
    ("sky", ["VENTO", "NUVEM", "TEMPESTADE", "TROVAO", "LUZ", "SOL"]),
    ("dojo", ["TERRA", "FERRO", "TITA", "JADE", "BIO", "SELVA", "OSSO", "SOMBRA",
              "AREIA", "DESERTO"]),
]

ROUND_NAMES = ["PRELIMINAR", "OITAVAS", "QUARTAS", "SEMIFINAL"]
ITEM_BY_TIER = [("repair_kit", 3), ("energy_cell", 3), ("shield_chip", 2),
                ("mega_repair", 3), ("power_chip", 2), ("revive_core", 2)]


def h(s, salt=""):
    return int(hashlib.md5((s + salt).encode()).hexdigest(), 16)


def arena_for(elem):
    for a, keys in ARENA_RULES:
        if elem in keys:
            return a
    return "dojo"


roster = json.load(open(ROSTER))
tier = {"bronze": 0, "silver": 1, "gold": 2}
order = sorted(roster, key=lambda r: (tier[r["r"]] * 1000 + h(r["i"], "ord") % 900))

pool_by_arena = {}
for r in roster:
    pool_by_arena.setdefault(arena_for(r["e"]), []).append(r["i"])

out = []
for n, r in enumerate(order):
    rid = r["i"]
    lvl = max(1, min(99, round(1 + 98 * (n / (len(order) - 1)) ** 1.18)))
    arena = arena_for(r["e"])
    nfights = 3 if lvl < 25 else 4
    # pool de inimigos: robos ja liberados (nivel <= atual) + base20
    unlocked = [x["i"] for x in order[:n]] + BASE20
    same = [x for x in pool_by_arena.get(arena, []) if x in unlocked]
    fights = []
    for f in range(nfights):
        count = 1 if (lvl < 4 and f == 0) else min(2 + (f >= nfights - 1), 3)
        picks = []
        for c in range(count):
            src = same if (same and (h(rid, f"a{f}{c}") % 3)) else unlocked
            picks.append(src[h(rid, f"e{f}{c}") % len(src)])
        boss = f == nfights - 1
        enemies = []
        for c, pid in enumerate(picks):
            enemies.append({"id": pid, "level": lvl + f, "trained": f})
        if boss:
            enemies.append({"id": rid, "level": min(99, lvl + f + 1), "trained": f + 1})
        name = f"FINAL — {r['n']}" if boss else ROUND_NAMES[min(f, 3)]
        fights.append({"name": name, "enemies": enemies})
    xp = round(120 * lvl ** 1.1)
    gold = round(xp * 5) + 300
    item, qty = ITEM_BY_TIER[min(5, lvl // 17)]
    # coordenadas no mapa espacial (mundo 3600x2400), rota em serpente com jitter
    per = 12
    row, col = n // per, n % per
    if row % 2:
        col = per - 1 - col
    x = 320 + col * 270 + (h(rid, "jx") % 90) - 45
    y = 260 + row * 250 + (h(rid, "jy") % 80) - 40
    station = f"station_{arena}_{1 + h(rid, 'st') % 3}"
    out.append({
        "id": f"t_{rid}",
        "name": f"COPA {r['n']}",
        "arena": arena,
        "element": r["e"],
        "desc": f"Circuito de {r['e'].title()} — enfrente {r['n']} na final e conquiste seu chassi.",
        "requiredLevel": lvl,
        "fights": fights,
        "reward": {"gold": gold, "xp": xp, "robot": rid, "item": item, "itemQty": qty},
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


body = ",\n".join("  " + ts(t, 1) for t in out)
src = ('import type { TournamentDef } from "./tournaments";\n\n'
       "// Gerado por assets/gen_tournaments.py — 1 torneio por robo novo.\n"
       "export const EXTRA_TOURNAMENTS: TournamentDef[] = [\n" + body + ",\n];\n")
open(OUT, "w").write(src)
print("torneios:", len(out), "| niveis:", out[0]["requiredLevel"], "->", out[-1]["requiredLevel"])
