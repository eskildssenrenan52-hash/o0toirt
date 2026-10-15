#!/usr/bin/env python3
"""E2E Fase G1 — carrossel de pets: setas, filtro, adocao, evolucao, slots."""
import json, time, sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:4200/"
SAVE_KEY = "campeoes-mecha-save-v1"

SAVE = {
    "version": 3,
    "playerLevel": 60,
    "playerXP": 0,
    "gold": 500000,
    "robots": [
        {"id": "aurorion", "level": 30, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
        {"id": "ferrovax", "level": 28, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
        {"id": "kagemaru", "level": 26, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
        {"id": "templarion", "level": 24, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}},
    ],
    "team": ["aurorion", "ferrovax", "kagemaru"],
    "items": {"repair_kit": 5, "energy_cell": 3},
    "wonTournaments": [],
    "battlesWon": 40,
    "loadouts": {},
    "gadgets": {},
    "pets": {"scrapmouse": 6},
    "activePet": "scrapmouse",
    "cards": [],
    "deck": [],
    "explorer": None,
    "mining": {"bars": {"ferro": 80, "cobre": 60}},
    "customs": [],
}

errors, broken = [], []


def click(page, text, nth=-1):
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
    time.sleep(0.45)
    return n


def arrow(page, label):
    n = page.evaluate(
        """(l) => {
        const e = [...document.querySelectorAll('button')].filter(b => b.getAttribute('aria-label') === l && !b.disabled);
        if (!e.length) return 0;
        e[e.length-1].click();
        return e.length;
    }""",
        label,
    )
    time.sleep(0.35)
    return n


def center_name(page):
    return page.evaluate(
        """() => {
        const b = [...document.querySelectorAll('img[alt]')].filter(i => i.alt && i.src.includes('/pets/'));
        return b.length ? b[b.length-1].alt : null;
    }"""
    )


def store(page):
    return page.evaluate(
        "(k) => JSON.parse(localStorage.getItem(k) || '{}')", SAVE_KEY
    )


with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 480, "height": 860})
    pg.on("console", lambda m: errors.append(f"console:{m.type}:{m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))
    pg.on(
        "response",
        lambda r: broken.append(f"{r.status} {r.url}") if r.status >= 400 else None,
    )

    pg.goto(URL, wait_until="domcontentloaded")
    pg.evaluate("([k,v]) => localStorage.setItem(k, JSON.stringify(v))", [SAVE_KEY, SAVE])
    pg.reload(wait_until="networkidle")
    time.sleep(3.5)

    # entra no rancho
    print("hub:", click(pg, "PETS") or click(pg, "RANCHO"))
    time.sleep(1.2)
    pg.screenshot(path="/tmp/pg1_a.png")
    n0 = center_name(pg)
    print("pet inicial:", n0)
    assert n0, "nenhum pet no palco"

    # setas de pet
    seq = [n0]
    for i in range(4):
        assert arrow(pg, "pet proximo"), "seta proximo ausente"
        seq.append(center_name(pg))
    print("sequencia >:", seq)
    assert len(set(seq)) >= 4, f"carrossel nao trocou de pet: {seq}"
    pg.screenshot(path="/tmp/pg1_b.png")

    for i in range(2):
        assert arrow(pg, "pet anterior"), "seta anterior ausente"
    back = center_name(pg)
    print("apos < <:", back, "esperado", seq[2])
    assert back == seq[2], f"volta errada: {back} != {seq[2]}"

    # setas de especie
    assert arrow(pg, "especie proxima")
    sp1 = center_name(pg)
    assert arrow(pg, "especie anterior")
    sp2 = center_name(pg)
    print("especie >>:", sp1, "<<:", sp2)
    assert sp1 != sp2, "setas de especie nao mudaram o pet"
    pg.screenshot(path="/tmp/pg1_c.png")

    # filtro
    assert click(pg, "TODOS"), "botao de filtro ausente"
    f1 = pg.evaluate("() => document.body.innerText.includes('MEUS')")
    print("filtro MEUS visivel:", f1)
    meus = center_name(pg)
    print("pet no filtro MEUS:", meus)
    pg.screenshot(path="/tmp/pg1_d.png")
    assert click(pg, "MEUS")  # -> A ADOTAR
    time.sleep(0.4)

    # adota o pet visivel no filtro "A ADOTAR"
    alvo = center_name(pg)
    before = store(pg)
    nb = len([k for k, v in (before.get("pets") or {}).items() if v > 0])
    assert click(pg, "ADOTAR"), "botao ADOTAR ausente"
    after = store(pg)
    na = len([k for k, v in (after.get("pets") or {}).items() if v > 0])
    print(f"adocao: {alvo} pets {nb} -> {na} ouro {before.get('gold')} -> {after.get('gold')}")
    assert na == nb + 1, "pet nao foi adotado"
    assert after["gold"] < before["gold"], "ouro nao foi cobrado"
    pg.screenshot(path="/tmp/pg1_e.png")

    # treina / evolui o adotado
    g0 = store(pg)["gold"]
    lv0 = max(store(pg)["pets"].values())
    assert click(pg, "TREINAR") or click(pg, "EVOLUIR"), "botao de treino ausente"
    st = store(pg)
    print("treino: ouro", g0, "->", st["gold"], "niveis", st["pets"])
    assert st["gold"] < g0, "treino nao cobrou ouro"

    # slots da equipe
    st = store(pg)
    print("activePets antes do LEVAR:", st.get("activePets"))
    assert click(pg, "LEVAR") or click(pg, "DISPENSAR"), "botao de slot ausente"
    st2 = store(pg)
    print("activePets depois:", st2.get("activePets"))
    assert st2.get("activePets") != st.get("activePets"), "slot nao mudou"
    pg.screenshot(path="/tmp/pg1_f.png")

    # evolucao de estagio: scrapmouse esta no Lv6 (fronteira) no save injetado
    while center_name(pg) != "RATO SUCATA":
        assert arrow(pg, "pet anterior"), "nao achei o RATO SUCATA"
    b0 = store(pg)
    bars0 = sum((b0.get("mining") or {}).get("bars", {}).values())
    assert click(pg, "EVOLUIR"), "botao EVOLUIR ausente no Lv6"
    b1 = store(pg)
    bars1 = sum((b1.get("mining") or {}).get("bars", {}).values())
    print("evolucao Lv6->7: lingotes", bars0, "->", bars1, "nivel", b1["pets"]["scrapmouse"])
    assert b1["pets"]["scrapmouse"] == 7, "nao evoluiu de estagio"
    assert bars1 < bars0, "evolucao nao cobrou lingotes"
    assert "ADULTO" in pg.evaluate("() => document.body.innerText"), "estagio ADULTO nao exibido"

    pg.evaluate("() => window.scrollTo(0,0)")
    time.sleep(0.3)
    pg.screenshot(path="/tmp/pg1_g.png")

    imgs = pg.evaluate(
        """() => { const a=[...document.images]; return [a.length, a.filter(i=>!i.complete||i.naturalWidth===0).length]; }"""
    )
    print("imagens:", imgs)
    print("erros:", errors[:8])
    print("http>=400:", [b for b in broken if "favicon" not in b][:8])
    assert imgs[1] == 0, "imagem quebrada"
    assert not errors, "erros de console"
    br.close()

print("OK G1")
