import json, time
from playwright.sync_api import sync_playwright

SAVE_KEY = "campeoes-mecha-save-v1"
OUT = "/tmp/e2e_cards2"
DECK = ["chama_viva", "forja_furiosa", "coroa_incandescente"]  # chama x3 -> sinergia


def jsclick(pg, text, exact=True, last=True):
    ok = pg.evaluate(
        """([t, exact, last]) => {
      const els = Array.from(document.querySelectorAll('button'));
      const hit = els.filter(e => (exact ? e.innerText.trim() === t : e.innerText.includes(t)) && !e.disabled);
      if (!hit.length) return false;
      (last ? hit[hit.length-1] : hit[0]).click();
      return true;
    }""",
        [text, exact, last],
    )
    time.sleep(1.2)
    return ok


SAVE = {
    "version": 2,
    "gold": 999999,
    "playerLevel": 60,
    "playerXP": 0,
    "robots": [
        {"id": i, "level": 30, "xp": 0, "trained": {"str": 0, "def": 0, "agl": 0}}
        for i in ("aurorion", "ferrovax", "cryolance", "voltronin")
    ],
    "team": ["aurorion", "ferrovax", "cryolance", "voltronin"],
    "items": {"repair_kit": 5, "energy_cell": 5},
    "wonTournaments": [],
    "battlesWon": 40,
    "cards": DECK + ["placa_bruta", "singularidade"],
    "deck": DECK,
}

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 780})
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))

    pg.goto("http://localhost:4200/", wait_until="domcontentloaded")
    pg.evaluate("([k,v]) => localStorage.setItem(k, v)", [SAVE_KEY, json.dumps(SAVE)])
    pg.reload(wait_until="networkidle")
    time.sleep(4)
    for _ in range(8):
        if pg.get_by_text("ENTRAR", exact=False).count():
            break
        try:
            pg.mouse.click(195, 700)
        except Exception:
            pass
        time.sleep(1)

    print("cards screen:", jsclick(pg, "SALAO DE CARDS"))
    time.sleep(2)
    pg.screenshot(path=f"{OUT}_01_deck.png", full_page=False)
    body = pg.inner_text("body")
    i = body.find("DECK 3/3")
    print("--- faixa deck ---")
    print(body[i : i + 500] if i >= 0 else body[:500])

    # abrir card do deck e remover/reequipar via modal
    pg.evaluate("() => document.querySelectorAll(\"button:has(img[src^='/cards/'])\")[3].click()")
    time.sleep(1.2)
    pg.screenshot(path=f"{OUT}_02_modal.png")
    btns = pg.evaluate(
        "Array.from(document.querySelectorAll('button')).map(b=>[b.innerText.trim(), b.disabled])"
    )
    print("botoes modal:", [x for x in btns if x[0] in ("REMOVER", "EQUIPAR", "FECHAR", "JA POSSUI") or "COMPRAR" in x[0]])
    print("removeu:", jsclick(pg, "REMOVER"))
    time.sleep(0.8)
    save = json.loads(pg.evaluate(f"localStorage.getItem({json.dumps(SAVE_KEY)})"))
    print("deck apos remover:", save.get("deck"))
    print("botoes pos-remover:", pg.evaluate("Array.from(document.querySelectorAll('button')).map(b=>[b.innerText.trim(), b.disabled]).filter(x=>x[0].length<20)"))
    print("reequipou:", jsclick(pg, "EQUIPAR"))
    time.sleep(0.8)
    save = json.loads(pg.evaluate(f"localStorage.getItem({json.dumps(SAVE_KEY)})"))
    print("deck apos reequipar:", save.get("deck"))
    jsclick(pg, "FECHAR")
    pg.screenshot(path=f"{OUT}_03_volta.png")

    # voltar ao hub e entrar na arena para uma batalha
    jsclick(pg, "VOLTAR", True, False)
    time.sleep(2)
    print("arena:", jsclick(pg, "ARENA", True, False))
    time.sleep(2.5)
    pg.screenshot(path=f"{OUT}_04_arena.png")
    body = pg.inner_text("body")
    print("--- arena ---")
    print(body[:400])

    broken = pg.evaluate(
        "Array.from(document.images).filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src)"
    )
    print("IMAGENS QUEBRADAS", broken)
    print("ERRORS", errs[:10])
    b.close()
