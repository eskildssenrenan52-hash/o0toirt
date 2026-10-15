#!/usr/bin/env python3
"""E2E G2 — confere que gadget MK + chips + refino de card mudam os numeros do combate."""
import json
import time
from playwright.sync_api import sync_playwright

URL = "http://localhost:4200/"
KEY = "campeoes-mecha-save-v1"

ROBOT = {"id": "aurorion", "level": 30, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}}

BASE = {
    "version": 3,
    "playerLevel": 60,
    "playerXP": 0,
    "gold": 900000,
    "robots": [ROBOT],
    "team": ["aurorion"],
    "items": {},
    "wonTournaments": [],
    "battlesWon": 40,
    "loadouts": {},
    "gadgets": {},
    "pets": {},
    "activePets": [],
    "cards": [],
    "deck": [],
    "cardRefine": {},
    "chips": [],
    "gadgetChips": {},
    "explorer": None,
    "mining": {"bars": {"ferro": 300, "cobre": 300, "titanio": 300}},
    "customs": [],
}

LOADED = dict(BASE)
LOADED = json.loads(json.dumps(BASE))
LOADED["gadgets"] = {"aurorion": 20}
LOADED["cards"] = ["chama_viva_rubro"]
LOADED["deck"] = ["chama_viva_rubro"]
LOADED["cardRefine"] = {"chama_viva_rubro": 8}
LOADED["chips"] = ["power_t4", "crit_t4"]
LOADED["gadgetChips"] = {"aurorion": ["power_t4", "crit_t4", None]}

PROBE = """async ([key, patch, robot]) => {
    const save = await import('/src/web/game/save.ts');
    const battle = await import('/src/web/game/battle.ts');
    // parte do estado inicial e sobrescreve so o que o teste controla
    save.setState((s) => ({ ...s, ...patch }));
    // teamSaves injeta gadgetLevel/loadout exatamente como a tela de batalha faz
    const rs = save.teamSaves(save.getState()).find((r) => r.id === robot.id) ?? robot;
    const f = battle.makeFighter(rs, false, 'p1');
    return {
      gadgetLevel: f.gadgetLevel,
      gadgetMk: f.gadgetMk,
      gadgetMods: f.gadgetMods,
      power: battle.gadgetBonus(f, 'power'),
      crit: battle.gadgetBonus(f, 'crit'),
      amp: battle.cardBonus(f, 'amp'),
      cards: f.cards,
      hp: f.maxHp,
      stats: { str: f.str, def: f.def, agl: f.agl },
    };
}"""

errors = []

with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 480, "height": 860})
    pg.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    pg.goto(URL, wait_until="domcontentloaded")
    time.sleep(1.0)

    bare = pg.evaluate(PROBE, [KEY, BASE, ROBOT])
    full = pg.evaluate(PROBE, [KEY, LOADED, ROBOT])
    print("sem gadget/cards:", json.dumps(bare))
    print("com MK-II + chips T4 + refino +7:", json.dumps(full))

    assert bare["power"] == 0 and bare["amp"] == 0, f"fighter cru nao deveria ter bonus: {bare}"
    assert full["gadgetLevel"] == 20 and full["gadgetMk"] == "MK-II", f"MK errado: {full}"
    assert full["power"] > 0, "gadget+chip de impacto nao entrou em power"
    assert full["crit"] > 0, "chip de mira nao entrou em crit"
    assert full["amp"] > 0, "card refinado nao aumentou o AMP do deck"
    assert full["stats"]["str"] > bare["stats"]["str"], "forca nao subiu com gadget/chips/cards"
    assert full["hp"] >= bare["hp"], "hp regrediu"
    assert not errors, f"erros: {errors}"

    # o chip realmente soma por cima do gadget puro
    no_chips = json.loads(json.dumps(LOADED))
    no_chips["gadgetChips"] = {"aurorion": [None, None, None]}
    plain = pg.evaluate(PROBE, [KEY, no_chips, ROBOT])
    print("so gadget (sem chips):", json.dumps(plain))
    assert full["power"] > plain["power"], "chips nao somaram ao gadget"
    assert plain["crit"] == 0, "crit deveria vir so do chip"

    # refino de card muda o numero
    low = json.loads(json.dumps(LOADED))
    low["cardRefine"] = {"chama_viva_rubro": 1}
    r1 = pg.evaluate(PROBE, [KEY, low, ROBOT])
    print("refino +0:", r1["amp"], "-> refino +7:", full["amp"])
    assert full["amp"] > r1["amp"], "refino nao escalou o card"
    br.close()

print("OK BATALHA G2")
