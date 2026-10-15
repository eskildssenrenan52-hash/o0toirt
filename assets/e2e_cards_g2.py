#!/usr/bin/env python3
"""E2E Fase G2 — cards selados + refino e gadgets MK/sockets/chips."""
import time
from playwright.sync_api import sync_playwright

URL = "http://localhost:4200/"
SAVE_KEY = "campeoes-mecha-save-v1"

SAVE = {
    "version": 3,
    "playerLevel": 60,
    "playerXP": 0,
    "gold": 900000,
    "robots": [
        {"id": "aurorion", "level": 30, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
        {"id": "ferrovax", "level": 28, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
        {"id": "kagemaru", "level": 26, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
    ],
    "team": ["aurorion", "ferrovax", "kagemaru"],
    "items": {"repair_kit": 5, "energy_cell": 3},
    "wonTournaments": [],
    "battlesWon": 40,
    "loadouts": {},
    # aurorion parado no Lv10 (fronteira MK-I->MK-II fica no 10->11)
    "gadgets": {"aurorion": 10},
    "pets": {},
    "activePets": [],
    "cards": [],
    "deck": [],
    "cardRefine": {},
    "chips": [],
    "gadgetChips": {},
    "explorer": None,
    "mining": {"bars": {"ferro": 300, "cobre": 220, "titanio": 120}},
    "customs": [],
}

errors, broken = [], []


def click(page, text):
    n = page.evaluate(
        """(t) => {
        const els = [...document.querySelectorAll('button')]
          .filter(e => !e.disabled && (e.textContent||'').toUpperCase().includes(t));
        if (!els.length) return 0;
        els[els.length - 1].click();
        return els.length;
    }""",
        text.upper(),
    )
    time.sleep(0.5)
    return n


def click_first(page, text):
    n = page.evaluate(
        """(t) => {
        const els = [...document.querySelectorAll('button')]
          .filter(e => !e.disabled && (e.textContent||'').toUpperCase().includes(t));
        if (!els.length) return 0;
        els[0].click();
        return els.length;
    }""",
        text.upper(),
    )
    time.sleep(0.5)
    return n


def store(page):
    return page.evaluate("(k) => JSON.parse(localStorage.getItem(k) || '{}')", SAVE_KEY)


def bars(page):
    return sum((store(page).get("mining") or {}).get("bars", {}).values())


# agrupa os botoes com arte de card pelo pai: a fileira de selos tem exatamente 7,
# a lista da loja tem uma linha por base. Evita depender de largura em px.
GROUPS_JS = """() => {
    const groups = new Map();
    for (const b of document.querySelectorAll('button')) {
      const img = b.querySelector('img');
      if (!img || !(img.getAttribute('src') || '').includes('/cards/')) continue;
      const p = b.parentElement;
      if (!groups.has(p)) groups.set(p, []);
      groups.get(p).push(b);
    }
    return [...groups.values()];
}"""


def seal_buttons(page):
    """Miniaturas de selo no modal de detalhe (fileira com 7 artes)."""
    return page.evaluate(
        f"""() => {{
        const gs = ({GROUPS_JS})();
        const row = gs.find(g => g.length === 7);
        return row ? row.length : 0;
    }}"""
    )


def click_seal(page, idx):
    n = page.evaluate(
        f"""(i) => {{
        const gs = ({GROUPS_JS})();
        const row = gs.find(g => g.length === 7);
        if (!row || row.length <= i) return 0;
        row[i].click();
        return row.length;
    }}""",
        idx,
    )
    time.sleep(0.4)
    return n


with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 480, "height": 860})
    pg.on("console", lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    pg.on("response", lambda r: broken.append(f"{r.status} {r.url}") if r.status >= 400 else None)

    pg.goto(URL, wait_until="domcontentloaded")
    pg.evaluate("([k,v]) => localStorage.setItem(k, JSON.stringify(v))", [SAVE_KEY, SAVE])
    pg.reload(wait_until="networkidle")
    time.sleep(3.5)

    # ---------------------------------------------------------- CARDS
    assert click(pg, "SALAO DE CARDS"), "botao do salao de cards ausente"
    time.sleep(1.2)
    txt = pg.evaluate("() => document.body.innerText")
    print("cabecalho:", [l for l in txt.split("\n") if "SELOS" in l][:2])
    assert "210 CARDS" in txt, f"contagem de cards nao exibida: {txt[:200]}"
    assert "DECK 0/5" in txt, f"slots de deck errados: {txt[:200]}"
    pg.screenshot(path="/tmp/g2_a.png")

    # abre a loja e escolhe o primeiro card
    assert click(pg, "LOJA"), "aba LOJA ausente"
    time.sleep(0.6)
    opened = pg.evaluate(
        f"""() => {{
        const gs = ({GROUPS_JS})();
        const list = gs.filter(g => g.length > 7).sort((a, b) => b.length - a.length)[0];
        if (!list) return 0;
        list[0].click();
        return list.length;
    }}"""
    )
    print("tiles de card na loja:", opened)
    assert opened, "nenhum card listado na loja"
    time.sleep(0.9)
    n_seals = seal_buttons(pg)
    print("miniaturas de selo no modal:", n_seals)
    assert n_seals >= 7, f"grid de selos nao renderizou ({n_seals})"
    pg.screenshot(path="/tmp/g2_b.png")

    # filtros CSS distintos por selo (recoloracao sem arte nova)
    filters = pg.evaluate(
        f"""() => {{
        const gs = ({GROUPS_JS})();
        const row = gs.find(g => g.length === 7) || [];
        return row.map(b => getComputedStyle(b.querySelector('img')).filter);
    }}"""
    )
    uniq = len(set(filters))
    print("filtros distintos:", uniq, filters[:3])
    assert uniq >= 6, f"selos nao recoloriram a arte: {filters}"

    # compra o selo BRUTO (indice 0)
    assert click_seal(pg, 0), "selo 0 nao clicavel"
    time.sleep(0.4)
    g0 = store(pg)["gold"]
    assert click(pg, "COMPRAR"), "botao COMPRAR ausente"
    st = store(pg)
    print(f"compra bruto: cards={st['cards']} ouro {g0} -> {st['gold']}")
    assert len(st["cards"]) == 1, "card nao foi comprado"
    assert st["gold"] < g0, "ouro nao foi cobrado"
    base_id = st["cards"][0]
    SEAL_IDS = ("rubro", "polar", "voltaico", "umbral", "aureo", "prisma")
    assert not base_id.endswith(SEAL_IDS), f"esperava selo bruto, veio {base_id}"

    # troca para um selo colorido e compra tambem
    assert click_seal(pg, 3), "selo 3 nao clicavel"
    time.sleep(0.4)
    assert click(pg, "COMPRAR"), "COMPRAR indisponivel no selo colorido"
    st = store(pg)
    sealed = [c for c in st["cards"] if c.endswith(SEAL_IDS)]
    print("cards apos 2a compra:", st["cards"])
    assert sealed, "variante selada nao foi comprada"
    sealed_id = sealed[0]
    assert sealed_id.startswith(base_id + "_"), f"{sealed_id} nao e variante de {base_id}"

    # equipa a variante selada
    assert click(pg, "EQUIPAR"), "botao EQUIPAR ausente"
    st = store(pg)
    print("deck:", st["deck"])
    assert st["deck"] == [sealed_id], f"deck errado: {st['deck']}"
    pg.screenshot(path="/tmp/g2_c.png")

    # refino: sobe ate cruzar o marco de lingotes (nivel 4)
    b0 = bars(pg)
    for i in range(3):
        g_before = store(pg)["gold"]
        assert click(pg, "REFINAR"), f"botao REFINAR ausente no passo {i}"
        st = store(pg)
        assert st["gold"] < g_before, f"refino {i} nao cobrou ouro"
    st = store(pg)
    b1 = bars(pg)
    print(f"refino: {st['cardRefine']} lingotes {b0} -> {b1}")
    assert st["cardRefine"].get(sealed_id) == 4, f"refino nao chegou a 4: {st['cardRefine']}"
    assert b1 < b0, "marco de refino nao cobrou lingotes"
    assert "REFINO +3" in pg.evaluate("() => document.body.innerText"), "refino nao exibido"
    pg.screenshot(path="/tmp/g2_d.png")

    assert click(pg, "FECHAR"), "botao FECHAR ausente"
    time.sleep(0.5)
    imgs = pg.evaluate(
        "() => { const a=[...document.images]; return [a.length, a.filter(i=>!i.complete||i.naturalWidth===0).length]; }"
    )
    print("imagens (cards):", imgs)
    assert imgs[1] == 0, "imagem quebrada na tela de cards"

    # volta ao hub
    assert click(pg, "◀") or click(pg, "VOLTAR") or click_first(pg, "◀"), "sem botao de voltar"
    time.sleep(1.5)

    # ---------------------------------------------------------- GADGETS / CHIPS
    assert click(pg, "OFICINA DO ENGENHEIRO"), "botao da oficina ausente"
    time.sleep(1.2)
    txt = pg.evaluate("() => document.body.innerText")
    assert "MAX Lv30" in txt, f"teto de nivel errado: {txt[:220]}"
    assert "MK-I" in txt, "marco MK nao exibido"
    print("oficina:", [l for l in txt.split("\n") if "SOCKETS EM" in l][:1])
    pg.screenshot(path="/tmp/g2_e.png")

    # forja um chip (tier 1, cobra ouro + lingotes)
    assert click(pg, "FORJA DE CHIPS"), "aba de chips ausente"
    time.sleep(0.8)
    cb0, gb0 = bars(pg), store(pg)["gold"]
    assert click_first(pg, "FORJAR"), "botao FORJAR ausente"
    st = store(pg)
    print(f"chip forjado: {st['chips']} ouro {gb0} -> {st['gold']} lingotes {cb0} -> {bars(pg)}")
    assert len(st["chips"]) == 1, "chip nao foi forjado"
    assert st["gold"] < gb0 and bars(pg) < cb0, "forja nao cobrou ouro+lingotes"
    chip_id = st["chips"][0]
    pg.screenshot(path="/tmp/g2_f.png")

    # volta para gadgets e sobe o gadget do Lv10 -> Lv11 (marco, cobra lingotes)
    assert click(pg, "GADGETS"), "aba GADGETS ausente"
    time.sleep(0.8)
    ub0, ug0 = bars(pg), store(pg)["gold"]
    assert click_first(pg, "+1"), "botao de upgrade ausente"
    st = store(pg)
    print(f"gadget: nivel {st['gadgets']} ouro {ug0} -> {st['gold']} lingotes {ub0} -> {bars(pg)}")
    assert st["gadgets"]["aurorion"] == 11, f"gadget nao subiu: {st['gadgets']}"
    assert bars(pg) < ub0, "marco MK-II nao cobrou lingotes"
    assert "MK-II" in pg.evaluate("() => document.body.innerText"), "MK-II nao exibido"

    # encaixa o chip num socket liberado (Lv11 libera 2 sockets: 5 e 15 -> so o 1o)
    opened_socket = pg.evaluate(
        """() => {
        const els = [...document.querySelectorAll('button')]
          .filter(b => !b.disabled && (b.textContent||'').trim() === '+');
        if (!els.length) return 0;
        els[0].click();
        return els.length;
    }"""
    )
    time.sleep(0.6)
    print("sockets abertos vazios:", opened_socket)
    assert opened_socket, "socket vazio nao clicavel"
    time.sleep(0.7)
    assert click_first(pg, "CHIP DE"), "lista de chips do socket vazia"
    st = store(pg)
    print("gadgetChips:", st["gadgetChips"])
    slots = st["gadgetChips"].get("aurorion") or []
    assert chip_id in slots, f"chip nao encaixou: {st['gadgetChips']}"
    time.sleep(0.6)
    pg.screenshot(path="/tmp/g2_g.png")

    # o efeito somado do chip aparece na ficha do gadget
    txt = pg.evaluate("() => document.body.innerText")
    print("resumo gadget:", [l for l in txt.split("\n") if "+" in l and l.isupper()][:4])

    imgs = pg.evaluate(
        "() => { const a=[...document.images]; return [a.length, a.filter(i=>!i.complete||i.naturalWidth===0).length]; }"
    )
    print("imagens (oficina):", imgs)
    print("erros:", errors[:8])
    print("http>=400:", [b for b in broken if "favicon" not in b][:8])
    assert imgs[1] == 0, "imagem quebrada na oficina"
    assert not errors, f"erros de console: {errors[:5]}"
    br.close()

print("OK G2")
