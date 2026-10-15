#!/usr/bin/env python3
"""Gera os 100 Blueprints novos e injeta em game/robots.ts."""
import json
import hashlib

ROSTER = "/home/user/mecha-champions/assets/roster100.json"
TS = "/home/user/mecha-champions/packages/web/src/web/game/robots.ts"

VFX_BY_ELEM = {
    "FOGO": ("VFX.explosion", "VFX.explosion"), "BRASA": ("VFX.explosion", "VFX.explosion"),
    "MAGMA": ("VFX.explosion", "VFX.explosion"), "CINZA": ("VFX.explosion", "VFX.void"),
    "GELO": ("VFX.slash", "VFX.shield"), "AGUA": ("VFX.slash", "VFX.heal"),
    "MAR": ("VFX.slash", "VFX.heal"), "VAPOR": ("VFX.impact", "VFX.heal"),
    "TROVAO": ("VFX.thunder", "VFX.thunder"), "TEMPESTADE": ("VFX.thunder", "VFX.thunder"),
    "RAIO": ("VFX.thunder", "VFX.thunder"), "ENERGIA": ("VFX.thunder", "VFX.levelup"),
    "LUZ": ("VFX.slash", "VFX.levelup"), "SOL": ("VFX.slash", "VFX.levelup"),
    "ESTELAR": ("VFX.levelup", "VFX.void"), "COSMICO": ("VFX.void", "VFX.levelup"),
    "VAZIO": ("VFX.void", "VFX.void"), "SOMBRA": ("VFX.void", "VFX.void"),
    "TREVAS": ("VFX.void", "VFX.void"), "TERRA": ("VFX.impact", "VFX.explosion"),
    "PEDRA": ("VFX.impact", "VFX.shield"), "FERRO": ("VFX.impact", "VFX.shield"),
    "METAL": ("VFX.impact", "VFX.shield"), "TITA": ("VFX.impact", "VFX.shield"),
    "BIO": ("VFX.slash", "VFX.heal"), "FLORA": ("VFX.slash", "VFX.heal"),
    "SELVA": ("VFX.slash", "VFX.heal"), "ACIDO": ("VFX.explosion", "VFX.void"),
    "VENENO": ("VFX.void", "VFX.void"), "AREIA": ("VFX.slash", "VFX.explosion"),
    "DESERTO": ("VFX.slash", "VFX.explosion"), "VENTO": ("VFX.slash", "VFX.thunder"),
    "CEU": ("VFX.slash", "VFX.levelup"), "TEMPO": ("VFX.void", "VFX.levelup"),
    "GRAVIDADE": ("VFX.void", "VFX.impact"), "MAGNETISMO": ("VFX.void", "VFX.thunder"),
    "CRISTAL": ("VFX.slash", "VFX.shield"), "JADE": ("VFX.slash", "VFX.heal"),
    "DIGITAL": ("VFX.thunder", "VFX.levelup"), "CIBER": ("VFX.thunder", "VFX.levelup"),
    "SOM": ("VFX.thunder", "VFX.void"), "PSIQUICO": ("VFX.void", "VFX.levelup"),
}

BASE = {
    "bronze": dict(hp=112, mp=88, str=104, def_=110, ag=88, mv=9, xv=9),
    "silver": dict(hp=104, mp=104, str=112, def_=102, ag=106, mv=11, xv=12),
    "gold": dict(hp=106, mp=116, str=122, def_=106, ag=110, mv=14, xv=15),
}

BIOS = [
    "Campeão de {e}. Sua técnica {s} encerra duelos em um golpe.",
    "Lenda do circuito de {e}. Ninguém sobrevive a {s} duas vezes.",
    "Chassi forjado para {e}. Abre a guarda inimiga com {s}.",
    "Veterano das arenas de {e}. Assina cada vitória com {s}.",
    "Piloto autônomo de {e}. Guarda {s} para o momento decisivo.",
    "Predador de {e}. Caça sistemas rivais e finaliza com {s}.",
]


def h(s, salt=""):
    return int(hashlib.md5((s + salt).encode()).hexdigest(), 16)


def vfx(elem):
    return VFX_BY_ELEM.get(elem, ("VFX.impact", "VFX.explosion"))


def ratios(r, rid):
    b = BASE[r]
    j = lambda k, spread: b[k] + (h(rid, k) % (2 * spread + 1)) - spread
    return dict(
        hp=j("hp", 8), mp=j("mp", 8), str=j("str", 8),
        def_=j("def_", 8), ag=j("ag", 9), mv=b["mv"], xv=b["xv"],
    )


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


roster = json.load(open(ROSTER))
out = []
for r in roster:
    rid, name, elem, rar = r["i"], r["n"], r["e"], r["r"]
    vs, vp = vfx(elem)
    ra = ratios(rar, rid)
    s = r["s"]
    bio = BIOS[h(rid, "bio") % len(BIOS)].format(e=elem, s=s[2])
    eff = r["f"]
    turns = 2 if eff == "paralyze" else 3
    power = {"paralyze": 0, "trapped": 0, "burn": 14, "poison": 16, "blind": 25,
             "weakening": 28, "drain": 15, "damage_reduction": 30,
             "adrenalin": 25, "hp_regen": 14}.get(eff, 20)
    chance = 0.5 if eff in ("paralyze", "trapped") else 0.75
    out.append(f"""  {{
    id: "{rid}",
    name: "{esc(name)}",
    element: "{elem}",
    rarity: "{rar}",
    ratios: {{ hp: {ra['hp']}, mp: {ra['mp']}, str: {ra['str']}, def: {ra['def_']}, ag: {ra['ag']}, mv: {ra['mv']}, xv: {ra['xv']} }},
    bio: "{esc(bio)}",
    vfxStrong: {vs},
    vfxSpecial: {vp},
    names: ["{esc(s[0])}", "{esc(s[1])}", "{esc(s[2])}", "{esc(s[3])}"],
    effect: {{ type: "{eff}", power: {power}, turns: {turns}, chance: {chance} }},
  }},""")

block = "\n".join(out)
src = open(TS).read()
marker = "\n];\n\nexport const ROBOTS"
assert marker in src, "marcador nao encontrado"
if "// --- ROSTER 100 ---" in src:
    head, rest = src.split("  // --- ROSTER 100 ---\n", 1)
    src = head + rest.split(marker, 1)[0].split("\n];\n")[0]
    raise SystemExit("ja injetado; rode git checkout antes")
src = src.replace(marker, "  // --- ROSTER 100 ---\n" + block + marker, 1)
open(TS, "w").write(src)
print("blueprints injetados:", len(out))
